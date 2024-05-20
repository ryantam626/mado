import ctypes
import ctypes.wintypes
import queue
import threading

import win32con
from loguru import logger

from mado.types_ import WINDOW_HANDLE
from mado.window_manager import events as wme
from mado.window import Window

# Some of these codes are not available in win32con for some reason. Define it ourselves
# https://learn.microsoft.com/en-us/windows/win32/winauto/event-constants
win32con.EVENT_OBJECT_CLOAKED = 0x8017
win32con.EVENT_OBJECT_UNCLOAKED = 0x8018


class WinEventHookListener(threading.Thread):

    def __init__(self, event_queue: queue.Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daemon = True
        self.event_queue = event_queue

    # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook
    def callback(
        self,
        hWinEventHook,  # noqa
        event,
        hwnd,
        idObject,  # noqa
        idChild,  # noqa
        dwEventThread,  # noqa
        dwmsEventTime,  # noqa
    ) -> None:
        wm_event = None
        if idObject == win32con.OBJID_WINDOW:
            window = Window(hwnd=WINDOW_HANDLE(hwnd))
            match event:
                # This is mostly ported from komorebi, we should eventually check this actually make sense for us too.
                case win32con.EVENT_OBJECT_DESTROY:
                    wm_event = wme.Destroy(event, window)
                case win32con.EVENT_OBJECT_HIDE:
                    wm_event = wme.Hide(event, window)
                case win32con.EVENT_OBJECT_CLOAKED:  # noqa
                    wm_event = wme.Cloak(event, window)
                case win32con.EVENT_SYSTEM_MINIMIZESTART:
                    wm_event = wme.Minimise(event, window)
                case win32con.EVENT_OBJECT_SHOW | win32con.EVENT_SYSTEM_MINIMIZEEND:
                    wm_event = wme.Show(event, window)
                case win32con.EVENT_OBJECT_UNCLOAKED:  # noqa
                    wm_event = wme.Uncloak(event, window)
                case win32con.EVENT_SYSTEM_FOREGROUND | win32con.EVENT_OBJECT_FOCUS:
                    wm_event = wme.FocusChange(event, window)
                case win32con.EVENT_SYSTEM_MOVESIZESTART:
                    wm_event = wme.MoveResizeStart(event, window)
                case win32con.EVENT_SYSTEM_MOVESIZEEND:
                    wm_event = wme.MoveResizeEnd(event, window)
                case win32con.EVENT_SYSTEM_CAPTURESTART | win32con.EVENT_SYSTEM_CAPTURESTART:
                    wm_event = wme.MouseCapture(event, window)
                case (
                    win32con.EVENT_OBJECT_NAMECHANGE
                ):  # TODO: Might need to handle this to handle some weird cases of window creation?
                    pass
                case win32con.EVENT_OBJECT_LOCATIONCHANGE:
                    wm_event = wme.Moved(event, window)
        if wm_event is not None:
            self.event_queue.put(wm_event)

    def run(self):
        logger.info("Starting win event listener...")
        user32 = ctypes.windll.user32
        ole32 = ctypes.windll.ole32
        # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook
        user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

        # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nc-winuser-wineventproc
        WinEventProcType = ctypes.WINFUNCTYPE(  # noqa
            None,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
        )
        ole32.CoInitialize(0)

        # ???: Need to create this first for some reason?
        win_event_proc = WinEventProcType(self.callback)

        user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE
        hook = user32.SetWinEventHook(
            win32con.EVENT_MIN,
            win32con.EVENT_MAX,
            0,
            win_event_proc,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT | win32con.WINEVENT_SKIPOWNPROCESS,
        )
        if hook == 0:
            exit(99)

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessageW(msg)
            user32.DispatchMessageW(msg)

        user32.UnhookWinEvent(hook)
        ole32.CoUninitialize()
