﻿import dataclasses
import enum

from mado.types_ import SCREEN_ID


@dataclasses.dataclass
class WindowManagerCommand:
    pass


@dataclasses.dataclass
class FocusVirtualDesktop(WindowManagerCommand):
    virtual_desktop_id: int


@dataclasses.dataclass
class SendToVirtualDesktop(WindowManagerCommand):
    virtual_desktop_id: int


class StateDump(WindowManagerCommand):
    """Dumping internal state of the window manager"""


@dataclasses.dataclass
class CycleFocusedWindow(WindowManagerCommand):
    """Cycle focused window in the same workspace."""

    class Direction(enum.Enum):
        forward = enum.auto()
        backward = enum.auto()

    direction: Direction


class Minimise(WindowManagerCommand):
    """Minimise the currently focused window."""


class ToggleMaximise(WindowManagerCommand):
    """Maximise the currently focused window."""


@dataclasses.dataclass
class MoveToScreen(WindowManagerCommand):
    """Move currently focused window to specified screen."""

    screen_id: SCREEN_ID


@dataclasses.dataclass
class SendToScreen(WindowManagerCommand):
    """Move currently focused window to specified screen."""

    screen_id: SCREEN_ID


@dataclasses.dataclass
class FocusScreen(WindowManagerCommand):
    """Focus specified screen."""

    screen_id: SCREEN_ID


@dataclasses.dataclass
class RecreateState(WindowManagerCommand):
    """Recreate state of the window manager.

    Useful for cases where window was create via unknown/unhandled means. (E.g. maybe firefox?)

    """

    pass


@dataclasses.dataclass
class TogglePinWindow(WindowManagerCommand):
    """Pin current window."""

    pass


@dataclasses.dataclass
class Noop(WindowManagerCommand):
    """Noop for silencing prefix hold down."""

    pass
