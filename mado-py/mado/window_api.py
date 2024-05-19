import ctypes
import ctypes.wintypes
import typing

import win32con
import win32gui
from pynput.mouse import Button, Controller
from win32api import SetCursorPos
from win32gui import GetForegroundWindow

from mado.types_ import COORDINATES_ISH, MONITOR_HANDLE


mouse = Controller()
dwmapi = ctypes.WinDLL("dwmapi")


def is_window_cloaked(hwnd: int) -> bool:
    res = ctypes.c_int(0)
    # https://github.com/LorenzCK/WindowsFormsAero/blob/master/src/WindowsFormsAero/Native/DwmWindowAttribute.cs
    DWMWA_CLOAKED = 14
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(res), ctypes.sizeof(res))
    return bool(res.value)


class TITLEBARINFO(ctypes.Structure):  # noqa
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcTitleBar", ctypes.wintypes.RECT),
        ("rgstate", ctypes.wintypes.DWORD * 6),  # noqa
    ]


def is_window_state_system_invisible(hwnd: int) -> int:
    # Title Info Initialization
    title_info = TITLEBARINFO()
    title_info.cbSize = ctypes.sizeof(title_info)
    ctypes.windll.user32.GetTitleBarInfo(hwnd, ctypes.byref(title_info))

    return title_info.rgstate[0] & win32con.STATE_SYSTEM_INVISIBLE


def get_monitor_handle_from_window(hwnd: int) -> MONITOR_HANDLE:
    return MONITOR_HANDLE(ctypes.windll.user32.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST))


def raise_and_focus_window(hwnd: int) -> None:
    foreground = GetForegroundWindow()
    if foreground == hwnd:
        return
    # send a dummy input to pass check, otherwise we can't focus the window for some reason.
    # ideally we should send a completely bogus input but i can't figure out how.
    mouse.release(Button.left)

    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        0,
        0,
        0,
        0,
        win32con.SWP_NOSIZE | win32con.SWP_NOMOVE | win32con.SWP_SHOWWINDOW,
    )
    win32gui.SetForegroundWindow(hwnd)


def centre_mouse_in_rect(rect) -> None:
    left, top, right, bottom = rect
    pos = (
        int((left + right) / 2),
        int((top + bottom) / 2),
    )
    SetCursorPos(pos)


def get_window_rect(hwnd: int) -> typing.Tuple[int, int, int, int]:
    # https://github.com/LorenzCK/WindowsFormsAero/blob/master/src/WindowsFormsAero/Native/DwmWindowAttribute.cs
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    res = ctypes.wintypes.RECT()
    status = dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(res), ctypes.sizeof(res)
    )
    if status != 0:
        res = win32gui.GetWindowRect(hwnd)
    else:
        res = (res.left, res.top, res.right, res.bottom)

    return res


def window_relative_move(
    hwnd: int, from_coordinates: COORDINATES_ISH, to_coordinates: COORDINATES_ISH
) -> None:
    offsets = (
        to_coordinates[0] - from_coordinates[0],
        to_coordinates[1] - from_coordinates[1],
    )
    requires_move = any(offsets)

    is_maximised = win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMAXIMIZED
    # We restore here because just setting the window pos while it being maximised causes weird issue later
    # e.g. upon minimised and maximised, it will be sent back to the original screen in the real world.
    if is_maximised and requires_move:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    rect = get_window_rect(hwnd)
    if requires_move:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            rect[0] + offsets[0],
            rect[1] + offsets[1],
            0,
            0,
            win32con.SWP_NOSIZE,
        )
    else:
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            0,
            0,
            0,
            0,
            win32con.SWP_NOSIZE | win32con.SWP_NOMOVE,
        )

    if is_maximised and requires_move:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)


def focus_desktop():
    # send a dummy input to pass check, otherwise we can't focus the window for some reason.
    # ideally we should send a completely bogus input but i can't figure out how.
    mouse.release(Button.left)
    win32gui.SetForegroundWindow(win32gui.GetDesktopWindow())


def window_max_toggle(hwnd: int) -> None:
    is_maximised = win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMAXIMIZED
    if is_maximised:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    else:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)


def minimise_window(hwnd: int) -> None:
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)


def restore_window(hwnd: int) -> None:
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)


def window_unstuck(hwnd: int) -> None:
    mouse.release(Button.left)
    is_maximised = win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMAXIMIZED
    if is_maximised:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        0,
        0,
        800,
        800,
        0,
    )
