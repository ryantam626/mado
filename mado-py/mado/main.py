from mado.window_manager import WindowManager


def run():
    try:
        WindowManager().run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
