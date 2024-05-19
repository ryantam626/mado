from typing import NewType, Tuple

SCREEN_ID = NewType("SCREEN_ID", str)
VIRTUAL_DESKTOP_ID = NewType("VIRTUAL_DESKTOP_ID", int)
WINDOW_HANDLE = NewType("WINDOW_HANDLE", int)
MONITOR_HANDLE = NewType("MONITOR_HANDLE", int)
COORDINATES_ISH = Tuple[int, int, int, int] | Tuple[int, int]
