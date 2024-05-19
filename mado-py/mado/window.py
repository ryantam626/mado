import dataclasses
import typing

from mado.config import DEFAULT_ORIGIN
from mado.types_ import WINDOW_HANDLE


@dataclasses.dataclass
class Window:
    hwnd: WINDOW_HANDLE
    # start x and start y of the screen that this window was last active on
    origin: typing.Optional[bool] = dataclasses.field(init=False, default=DEFAULT_ORIGIN, compare=False)
