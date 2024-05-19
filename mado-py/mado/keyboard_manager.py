import queue
import typing

from loguru import logger
from pynput import keyboard

from mado.types_ import SCREEN_ID, VIRTUAL_DESKTOP_ID
from mado.window_manager import commands

parse = keyboard.HotKey.parse


class Keybind:

    def __init__(self, keys: str, command: commands.WindowManagerCommand):
        self._keys = set(parse(keys))
        self._command = command

    def maybe_activate(self, keys: typing.Set[keyboard.KeyCode], event_queue: queue.Queue) -> bool:
        if keys >= self._keys:
            event_queue.put(self._command)
            return True
        return False


class KeyboardManager(keyboard.Listener):

    # This is manually ordered, so list the most specific ones first.
    KEYBINDS = [
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+1", commands.SendToVirtualDesktop(VIRTUAL_DESKTOP_ID(1))),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+2", commands.SendToVirtualDesktop(VIRTUAL_DESKTOP_ID(2))),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+3", commands.SendToVirtualDesktop(VIRTUAL_DESKTOP_ID(3))),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+4", commands.SendToVirtualDesktop(VIRTUAL_DESKTOP_ID(4))),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+5", commands.SendToVirtualDesktop(VIRTUAL_DESKTOP_ID(5))),
        Keybind("<ctrl>+<alt>+<cmd>+1", commands.FocusVirtualDesktop(VIRTUAL_DESKTOP_ID(1))),
        Keybind("<ctrl>+<alt>+<cmd>+2", commands.FocusVirtualDesktop(VIRTUAL_DESKTOP_ID(2))),
        Keybind("<ctrl>+<alt>+<cmd>+3", commands.FocusVirtualDesktop(VIRTUAL_DESKTOP_ID(3))),
        Keybind("<ctrl>+<alt>+<cmd>+4", commands.FocusVirtualDesktop(VIRTUAL_DESKTOP_ID(4))),
        Keybind("<ctrl>+<alt>+<cmd>+5", commands.FocusVirtualDesktop(VIRTUAL_DESKTOP_ID(5))),
        Keybind("<ctrl>+<alt>+<cmd>+t", commands.ToggleMaximise()),
        Keybind("<ctrl>+<alt>+<cmd>+g", commands.Minimise()),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+u", commands.MoveToScreen(SCREEN_ID("LEFT"))),
        Keybind("<ctrl>+<alt>+<cmd>+<shift>+i", commands.MoveToScreen(SCREEN_ID("RIGHT"))),
        Keybind("<ctrl>+<alt>+<cmd>+u", commands.FocusScreen(SCREEN_ID("LEFT"))),
        Keybind("<ctrl>+<alt>+<cmd>+i", commands.FocusScreen(SCREEN_ID("RIGHT"))),
        Keybind("<ctrl>+<alt>+<cmd>+r", commands.StateDump()),
        Keybind(
            "<ctrl>+<alt>+<cmd>+j",
            commands.CycleFocusedWindow(commands.CycleFocusedWindow.Direction.forward),
        ),
        Keybind(
            "<ctrl>+<alt>+<cmd>+k",
            commands.CycleFocusedWindow(commands.CycleFocusedWindow.Direction.backward),
        ),
    ]

    def __init__(self, event_queue: queue.Queue, *args, **kwargs) -> None:
        self._keys = set()
        self._event_queue = event_queue
        super().__init__(on_press=self._on_press, on_release=self._on_release, *args, **kwargs)

    def _on_press(self, key):
        previous = len(self._keys)
        self._keys.add(self.canonical(key))
        after = len(self._keys)
        if previous != after:
            for keybind in self.KEYBINDS:
                if keybind.maybe_activate(self._keys, self._event_queue):
                    break

    def _on_release(self, key):
        self._keys.discard(self.canonical(key))

    def run(self):
        logger.info("Starting keyboard manager...")
        super().run()
