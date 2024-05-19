import dataclasses
import typing

from mado.window import Window


@dataclasses.dataclass
class WindowManagerEvent:
    win_event: typing.Optional[int]
    window: Window


class Destroy(WindowManagerEvent):
    pass


class FocusChange(WindowManagerEvent):
    pass


class Hide(WindowManagerEvent):
    pass


class Cloak(WindowManagerEvent):
    pass


class Minimise(WindowManagerEvent):
    pass


class Show(WindowManagerEvent):
    pass


class Uncloak(WindowManagerEvent):
    pass


class MoveResizeStart(WindowManagerEvent):
    pass


class MoveResizeEnd(WindowManagerEvent):
    pass


class MouseCapture(WindowManagerEvent):
    pass


class Moved(WindowManagerEvent):
    pass
