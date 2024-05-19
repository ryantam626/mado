import dataclasses
import typing

from mado.config import DEFAULT_ORIGIN
from mado.types_ import WINDOW_HANDLE

if typing.TYPE_CHECKING:
    from mado.window_manager import Screen


@dataclasses.dataclass
class Window:
    hwnd: WINDOW_HANDLE
    # screen information which we can attach in internal logic/states, will not be used to compare.
    screen: typing.Optional["Screen"] = dataclasses.field(init=False, default=None, repr=False, compare=False)
    # start x and start y of the screen that this window was last active on
    origin: typing.Optional[bool] = dataclasses.field(init=False, default=DEFAULT_ORIGIN, compare=False)
