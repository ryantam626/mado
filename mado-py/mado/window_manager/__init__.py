import queue
from itertools import zip_longest

import pyvda
from loguru import logger

from mado import window_api
from mado.config import MOUSE_FOLLOWS_FOCUS, VIRTUAL_DESKTOP_IDS
from mado.keyboard_manager import KeyboardManager
from mado.win_event_listener import WinEventHookListener
from mado.window import Window
from mado.window_manager import commands
from mado.window_manager import events
from mado.window_manager.state import Screen, WindowManagerState


class WindowManager:

    def __init__(self) -> None:
        self.event_queue = queue.Queue()
        self.win_event_listener = WinEventHookListener(event_queue=self.event_queue)
        self.keyboard_manager = KeyboardManager(event_queue=self.event_queue)

        self.state = WindowManagerState.new()
        self.should_not_manage_next_focus = False

        self.maybe_populate_virtual_desktop()

    @staticmethod
    def maybe_populate_virtual_desktop() -> None:
        for virtual_desktop_id, virtual_desktop in zip_longest(
            VIRTUAL_DESKTOP_IDS, pyvda.get_virtual_desktops()
        ):
            if virtual_desktop is None:
                pyvda.VirtualDesktop.create()

    def run(self) -> None:
        logger.info("Starting Mado WindowManager...")
        self.win_event_listener.start()
        self.keyboard_manager.start()
        self.event_processing_loop()

    def event_processing_loop(self) -> None:
        logger.info("Starting event processing loop")
        while True:
            try:
                event = self.event_queue.get(timeout=0.5)  # timeout for a quicker sigint handling.
            except queue.Empty:
                continue

            if isinstance(event, events.WindowManagerEvent):
                self.handle_window_manager_event(event)
            elif isinstance(event, commands.WindowManagerCommand):
                self.handle_window_manager_command(event)
            else:
                pass

    def handle_window_manager_event(self, event: events.WindowManagerEvent) -> None:
        # make sure we have the correct focused screen first.
        if isinstance(event, (events.FocusChange, events.Show, events.MoveResizeEnd)):
            self.state.set_focused_screen_id(
                monitor_handle=window_api.get_monitor_handle_from_window(event.window.hwnd)
            )

        if isinstance(event, events.FocusChange):
            self.state.set_focused_window(event.window)

        if isinstance(event, events.Destroy):
            maybe_window_to_focus = self.state.unregister_window(event.window.hwnd)
            if maybe_window_to_focus is not None:
                self.composited_focus_window(maybe_window_to_focus)
        elif isinstance(event, (events.Minimise, events.Hide)):
            self.state.unregister_window(event.window.hwnd)
        elif isinstance(event, (events.Show, events.Uncloak)):
            self.state.register_window(event.window.hwnd)
        elif isinstance(event, events.MoveResizeEnd):
            self.state.force_register_window(event.window.hwnd)
        elif isinstance(event, events.Moved):
            if self.state.query_is_window_registered(event.window.hwnd):
                self.state.force_register_window(event.window.hwnd)

    def handle_window_manager_command(self, event: commands.WindowManagerCommand) -> None:
        # logger.debug("Handling window manager command, {} (State: {})", event, self)

        if isinstance(event, commands.FocusVirtualDesktop):
            pyvda.VirtualDesktop(number=event.virtual_desktop_id).go()
            # fully reset state, tracking state changes as we move virtual desktop is more pain than it's worth.
            self.state = WindowManagerState.new()
            if window_to_focus := self.state.focused_screen.focused_window:
                self.composited_focus_window(window_to_focus)
        elif isinstance(event, commands.SendToVirtualDesktop):
            if window_to_move := self.state.focused_screen.focused_window:
                pyvda.AppView(hwnd=window_to_move.hwnd).move(
                    pyvda.VirtualDesktop(number=event.virtual_desktop_id)
                )
        elif isinstance(event, commands.StateDump):
            logger.info("State dump: {}", self.state)
        elif isinstance(event, commands.CycleFocusedWindow):
            maybe_window_to_focus = self.state.command__cycle_window(event.direction)
            if maybe_window_to_focus is not None:
                self.composited_focus_window(maybe_window_to_focus)
        elif isinstance(event, (commands.SendToScreen, commands.MoveToScreen)):
            res = self.state.command__move_to_screen(screen_id=event.screen_id)
            if res is not None and res[1] != res[2]:  # from_screen != to_screen
                window_to_move_and_focus, from_screen, to_screen = res
                window_api.window_relative_move(
                    window_to_move_and_focus.hwnd, from_screen.size, to_screen.size
                )
                if isinstance(event, commands.MoveToScreen):
                    self.composited_focus_window(window_to_move_and_focus)
                else:
                    window_api.centre_mouse_in_rect(self.state.focused_screen.work_area_size)
                    window_api.focus_desktop()
        elif isinstance(event, commands.FocusScreen):
            maybe_window_to_focus = self.state.command__focus_screen(screen_id=event.screen_id)
            if maybe_window_to_focus is not None:
                self.composited_focus_window(maybe_window_to_focus)
            else:
                window_api.centre_mouse_in_rect(self.state.focused_screen.work_area_size)
                window_api.focus_desktop()
        elif isinstance(event, commands.Minimise):
            maybe_window_to_toggle = self.state.focused_screen.focused_window
            if maybe_window_to_toggle is not None:
                window_api.minimise_window(maybe_window_to_toggle.hwnd)
        elif isinstance(event, commands.ToggleMaximise):
            maybe_window_to_toggle = self.state.focused_screen.focused_window
            if maybe_window_to_toggle is not None:
                window_api.window_max_toggle(maybe_window_to_toggle.hwnd)
        elif isinstance(event, commands.RecreateState):
            logger.info("Recreating state...")
            self.state = WindowManagerState.new()

    def composited_focus_window(self, window: Window) -> None:
        try:
            window_api.raise_and_focus_window(window.hwnd)
            if MOUSE_FOLLOWS_FOCUS:
                window_api.centre_mouse_in_rect(window_api.get_window_rect(window.hwnd))
        except Exception as exc:
            logger.critical("Boom. Exception: {}", exc)
            # fully reset state upon failure, cba to figure out what went wrong.
            self.state = WindowManagerState.new()
