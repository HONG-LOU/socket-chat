import os
import sys

from PyQt6 import QtCore, QtWidgets

from .ui import MainApp
from dotenv import load_dotenv
from .async_runner import AsyncioRunner


def run() -> None:
    load_dotenv()
    api_base = os.environ.get("API_BASE", "http://127.0.0.1:8000")
    ws_url = os.environ.get("WS_URL", "ws://127.0.0.1:8000/ws")

    app = QtWidgets.QApplication(sys.argv)
    AsyncioRunner.instance().start()

    # 加载全局样式
    try:
        from pathlib import Path

        qss_path = Path(__file__).with_name("style.qss")
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    except Exception:
        pass

    w = MainApp(api_base, ws_url)
    w.resize(600, 400)
    w.show()

    app.exec()
    AsyncioRunner.instance().stop()


if __name__ == "__main__":
    run()
