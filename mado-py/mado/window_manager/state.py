import dataclasses
import typing
from itertools import zip_longest

from win32api import EnumDisplayMonitors, GetMonitorInfo

from mado.config import INIT_FOCUSED_SCREEN_ID, SCREEN_IDS
from mado.types_ import MONITOR_HANDLE, SCREEN_ID, WINDOW_HANDLE
from mado.window import Window


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
        return state
