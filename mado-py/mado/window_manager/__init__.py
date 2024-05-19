import queue

from loguru import logger

from mado.keyboard_manager import KeyboardManager
from mado.win_event_listener import WinEventHookListener
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

    def run(self) -> None:
        logger.info("Starting Mado WindowManager...")
        self.win_event_listener.start()
        self.keyboard_manager.start()
        self.event_processing_loop()

    def event_processing_loop(self) -> None:
        logger.info("Starting event processing loop")
        while True:
            event = self.event_queue.get()

            if isinstance(event, events.WindowManagerEvent):
                self.handle_window_manager_event(event)
            elif isinstance(event, commands.WindowManagerCommand):
                self.handle_window_manager_command(event)
            else:
                pass

    def handle_window_manager_event(self, event: events.WindowManagerEvent) -> None:
        logger.debug("Handling window manager event, {} (State: {})", event, self)

    def handle_window_manager_command(self, event: commands.WindowManagerCommand) -> None:
        logger.debug("Handling window manager command, {} (State: {})", event, self)
