import dataclasses
import typing
from itertools import zip_longest

import win32gui
import zipper
from loguru import logger
from win32api import EnumDisplayMonitors, GetMonitorInfo

from mado import window_api
from mado.config import IGNORED_WINDOW_TITLES, INIT_FOCUSED_SCREEN_ID, SCREEN_IDS
from mado.types_ import MONITOR_HANDLE, SCREEN_ID, WINDOW_HANDLE
from mado.window import Window
from mado.window_manager import commands

WINDOW_AT_CURSOR = object()


@dataclasses.dataclass
class Screen:
    """A physical screen(display/monitor)."""

    # win api sourced fields
    handle: int
    size: typing.Tuple[int, int, int, int]
    work_area_size: typing.Tuple[int, int, int, int]
    name: str

    #
    screen_id: SCREEN_ID
    cursor: zipper.Loc = dataclasses.field(
        default=zipper.list([]),
        repr=False,
    )

    @property
    def focused_window(self) -> typing.Optional[Window]:
        current = self.cursor.current
        return current if current else None

    @property
    def windows(self) -> typing.List[Window]:
        return list(self.cursor.top().children())

    @classmethod
    def from_handle(cls, handle: int, screen_id: SCREEN_ID) -> "Screen":
        monitor_info = GetMonitorInfo(handle)
        area = monitor_info["Monitor"]
        work_area_size = monitor_info["Work"]
        name = monitor_info["Device"].replace("\\\\.\\", "")

        return Screen(
            handle=handle,
            size=area,
            work_area_size=work_area_size,
            name=name,
            screen_id=screen_id,
        )

    def add_window(self, window: Window) -> None:
        window.workspace = self
        if self.cursor.at_end():
            self.cursor = self.cursor.append(window).down()
        else:
            self.cursor = self.cursor.insert_left(window).left()

    def remove_window(self, window: Window = WINDOW_AT_CURSOR) -> None:
        if window == WINDOW_AT_CURSOR:
            if self.cursor.at_end():
                logger.critical("Cannot remove focused window in an empty workspace")
                return
            else:
                self.cursor = self.cursor.remove()
                # potential edge case where it went up one?
                if self.cursor.at_end() and self.cursor.current:
                    self.cursor = self.cursor.down()
        else:
            new_cursor = (
                self.cursor
                if self.cursor.node() == window
                else self.cursor.find(lambda loc: loc.node() == window)
            )
            if new_cursor is None:
                logger.critical("Can't find window {} to remove in workspace {}", window, self)
            else:
                self.cursor = new_cursor
                self.remove_window()

    def focus_window(self, window: Window, raise_on_not_found: bool = True) -> None:
        new_cursor = self.cursor.top().find(lambda loc: loc.node() == window)
        if raise_on_not_found and new_cursor is None:
            raise ValueError(f"Can't find window {window}")
        if new_cursor is not None:
            self.cursor = new_cursor

    def cycle_window(self, direction: commands.CycleFocusedWindow.Direction) -> None:
        if direction is commands.CycleFocusedWindow.Direction.forward:
            right = self.cursor.right() or self.cursor.top().down()
            if right and right.current is not None:
                self.cursor = right
            else:
                self.cursor = self.cursor.top()
        elif direction is commands.CycleFocusedWindow.Direction.backward:
            left = self.cursor.left() or self.cursor.top().rightmost_descendant()
            if left and left.current is not None:
                self.cursor = left
            else:
                self.cursor = self.cursor.top()
        else:
            raise NotImplementedError()

    def __repr__(self) -> str:
        return (
            f"Screen("
            f"screen_id={self.screen_id}"
            f", handle={self.handle}"
            f", work_area_size={self.work_area_size}"
            f", name={self.name}"
            f", screen_id={self.screen_id}"
            f", windows={self.windows}"
            f", focused_window={self.focused_window})"
        )


@dataclasses.dataclass
class WindowManagerState:
    windows: typing.Dict[WINDOW_HANDLE, Window]
    screens: typing.Dict[SCREEN_ID, Screen]
    screens_by_monitor_handle: typing.Dict[MONITOR_HANDLE, Screen]
    focused_screen_id: SCREEN_ID

    @property
    def focused_screen(self) -> Screen:
        return self.screens[self.focused_screen_id]

    @classmethod
    def new(cls) -> "WindowManagerState":
        windows = {}
        screens = {}
        screens_by_handle = {}
        for display_monitor, screen_id in zip_longest(EnumDisplayMonitors(), SCREEN_IDS):
            if display_monitor and screen_id is None:
                raise RuntimeError("Not enough screen IDs.")

            if display_monitor is not None:
                (monitor_handle, _, _) = display_monitor
                screen = Screen.from_handle(monitor_handle, screen_id)
                screens[screen_id] = screen
                screens_by_handle[MONITOR_HANDLE(int(monitor_handle))] = screen

        focused_screen_id = INIT_FOCUSED_SCREEN_ID
        state = WindowManagerState(windows, screens, screens_by_handle, focused_screen_id)
        state.init_enum_windows()
        return state

    def init_enum_windows(self):
        init_window_handles = []

        def register_window(hwnd, lParam):  # noqa
            init_window_handles.append(WINDOW_HANDLE(hwnd))

        win32gui.EnumWindows(register_window, None)
        for handle in init_window_handles[::-1]:
            self.register_window(handle)

    def set_focused_screen_id(
        self,
        screen_id: typing.Optional[SCREEN_ID] = None,
        monitor_handle: typing.Optional[MONITOR_HANDLE] = None,
    ) -> None:
        if screen_id:
            self.focused_screen_id = screen_id
        elif monitor_handle:
            self.focused_screen_id = self.screens_by_monitor_handle[monitor_handle].screen_id
        else:
            raise ValueError("Missing input.")

    def set_focused_window(self, window: Window) -> None:
        try:
            if screen := self.windows.get(window.hwnd, window).screen:
                screen.focus_window(window, raise_on_not_found=True)
                return
        except ValueError:
            pass

        logger.critical(
            "Invalid window {} workspace information, iterating over all screen to set focused window.",
            window,
        )

        for screen in self.screens.values():
            screen.focus_window(window, raise_on_not_found=False)

    def register_window(self, handle: WINDOW_HANDLE) -> None:
        if handle in self.windows:
            logger.critical("Duplicated window {} found. Not registering.", handle)
            return

        is_visible = bool(win32gui.IsWindowVisible(handle))
        is_window = bool(win32gui.IsWindow(handle))
        is_minimised = bool(win32gui.IsIconic(handle))
        is_cloaked = bool(window_api.is_window_cloaked(handle))
        is_state_system_invisible = bool(window_api.is_window_state_system_invisible(handle))
        text = win32gui.GetWindowText(handle)

        if (
            is_visible
            and is_window
            and not is_cloaked
            and not is_minimised
            and not is_state_system_invisible
            and text
            and text not in IGNORED_WINDOW_TITLES
        ):
            logger.debug("Registering window {}", handle)
            window = Window(handle)
            monitor_handle = window_api.get_monitor_handle_from_window(handle)
            screen = self.screens_by_monitor_handle[monitor_handle]
            screen.add_window(window)
            self.windows[handle] = window
            window.screen = screen

    def force_register_window(self, handle: WINDOW_HANDLE) -> None:
        logger.debug("Force registering window {}", handle)
        if handle in self.windows:
            logger.debug("Found registered window {}, removing.", handle)
            old_window = self.windows.pop(handle)
            old_window.screen.remove_window(old_window)

        window = Window(handle)
        monitor_handle = window_api.get_monitor_handle_from_window(handle)
        self.windows[handle] = window
        screen = self.screens_by_monitor_handle[monitor_handle]
        screen.add_window(window)
        window.screen = screen
        self.focused_screen_id = screen.screen_id

    def unregister_window(self, handle: WINDOW_HANDLE) -> typing.Optional[Window]:
        window = self.windows.pop(handle, None)
        if window is None:
            logger.info("Un-registered window {} - skipping unregister.", handle)
            return

        window.screen.remove_window(window=window)
        return window.screen.focused_window

    def query_is_window_registered(self, handle: WINDOW_HANDLE) -> bool:
        return self.windows.get(handle, None) is not None

    def command__cycle_window(
        self, direction: commands.CycleFocusedWindow.Direction
    ) -> typing.Optional[Window]:
        self.focused_screen.cycle_window(direction)
        return self.focused_screen.focused_window

    def command__move_to_screen(
        self, screen_id: SCREEN_ID
    ) -> typing.Optional[typing.Tuple[Window, Screen, Screen]]:
        current_screen = self.focused_screen
        current_window = current_screen.focused_window
        target_screen = self.screens[screen_id]

        if isinstance(current_window, Window):
            current_screen.remove_window(current_window)
            target_screen.add_window(current_window)
            return (
                current_window,
                current_screen,
                target_screen,
            )

    def command__focus_screen(self, screen_id: SCREEN_ID) -> typing.Optional[Window]:
        self.focused_screen_id = screen_id
        return self.focused_screen.focused_window
