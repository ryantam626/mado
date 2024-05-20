import sys

from loguru import logger

from mado.window_manager import WindowManager


def run():
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    try:
        WindowManager().run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
