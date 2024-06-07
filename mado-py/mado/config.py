from mado.types_ import SCREEN_ID, VIRTUAL_DESKTOP_ID

VIRTUAL_DESKTOP_IDS = [
    VIRTUAL_DESKTOP_ID(1),  # Editor
    VIRTUAL_DESKTOP_ID(4),  # Music
    VIRTUAL_DESKTOP_ID(2),  # Terminal
    VIRTUAL_DESKTOP_ID(3),  # Browser
    VIRTUAL_DESKTOP_ID(5),  # Misc
]

SCREEN_IDS = [
    SCREEN_ID("MID"),
    SCREEN_ID("LEFT"),
    SCREEN_ID("RIGHT"),
    SCREEN_ID("TOP"),
]
INIT_FOCUSED_SCREEN_ID = SCREEN_IDS[0]

IGNORED_WINDOW_TITLES = {
    "Task Switching",
    "Chrome Legacy Window",
    "Citrix Workspace",
}

MOUSE_FOLLOWS_FOCUS = True

DEFAULT_ORIGIN = (0, 0)
