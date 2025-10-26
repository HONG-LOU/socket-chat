import os
import sys
from pathlib import Path


def _patch_qt_paths_for_frozen() -> None:
    """在冻结环境下，优先将 Qt 的 bin/plugins 加入 DLL 搜索路径，避免 QtCore 加载失败。"""
    try:
        if hasattr(sys, "_MEIPASS"):
            base = Path(getattr(sys, "_MEIPASS"))
            qtbin = base / "PyQt6" / "Qt6" / "bin"
            qtplugins = base / "PyQt6" / "Qt6" / "plugins"
            if qtbin.exists():
                try:
                    os.add_dll_directory(str(qtbin))
                except Exception:
                    os.environ["PATH"] = (
                        str(qtbin) + os.pathsep + os.environ.get("PATH", "")
                    )
            if qtplugins.exists():
                os.environ["QT_PLUGIN_PATH"] = str(qtplugins)
    except Exception:
        pass


_patch_qt_paths_for_frozen()

from PyQt6 import QtCore, QtWidgets

try:
    from .ui import MainApp
except ImportError:
    from client.ui import MainApp
from dotenv import load_dotenv

try:
    from .async_runner import AsyncioRunner
except ImportError:
    from client.async_runner import AsyncioRunner


# 内置默认后端地址，零配置可运行（可被环境变量覆盖）
DEFAULT_API_BASE = "http://8.156.77.141:8000"
DEFAULT_WS_URL = "ws://8.156.77.141:8000/ws"


# 内置样式（当找不到外部 style.qss 时回退使用）
EMBEDDED_QSS = """/* 全局基础 */
QWidget {
  background: #0e1016;
  color: #e6e8ef;
  font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
  font-size: 14px;
}

QLineEdit, QTextEdit, QListWidget, QComboBox {
  background: #151823;
  border: 1px solid #23283b;
  border-radius: 8px;
  padding: 8px 10px;
  selection-background-color: #2e6df6;
}

QPushButton {
  background: #2a3252;
  border: 1px solid #3b4570;
  border-radius: 8px;
  padding: 8px 14px;
}
QPushButton:hover { background: #343d63; }
QPushButton:pressed { background: #2b3358; }

/* 卡片容器 */
#Card {
  background: #121521;
  border: 1px solid #22263a;
  border-radius: 14px;
}

/* 顶部栏 */
#TopBar {
  background: #0f1422;
  border-bottom: 1px solid #1e2743;
}
#TopBar QLabel#Title {
  font-size: 16px;
  font-weight: 600;
}

/* 好友列表：分隔线与边界感 */
QListWidget#FriendsList {
  outline: none;
  border: 1px solid #23283b;
  border-radius: 10px;
  background: #121624;
}
QListWidget#FriendsList::item {
  padding: 12px 14px;
  border-bottom: 1px solid #1e2440;
}
QListWidget#FriendsList::item:last-child {
  border-bottom: none;
}
QListWidget#FriendsList::item:selected {
  background: #19213a;
}

/* 聊天气泡容器 */
QFrame#BubbleMe {
  background: #3b6df0;
  border-radius: 12px;
  padding: 8px 12px;
  color: #ffffff;
}
QFrame#BubbleMe QLabel { background: transparent; color: #ffffff; }
QFrame#BubblePeer {
  background: #171c2b;
  border-radius: 12px;
  padding: 8px 12px;
  color: #dfe3f1;
  border: 1px solid #232d4b;
}
QFrame#BubblePeer QLabel { background: transparent; color: #dfe3f1; }

/* 聊天区域背景与文本协调 */
QWidget#ChatArea {
  background: #0f1422;
}

/* 滚动区域视口透明，避免出现黑底 */
QAbstractScrollArea, QScrollArea { background: transparent; }
QWidget#qt_scrollarea_viewport { background: transparent; }
"""


def _find_stylesheet_path() -> Path | None:
    """优先从冻结目录或源码同级目录查找 style.qss。"""
    try:
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller 解包目录，spec 中 datas 目标为 'client'
            frozen_path = Path(getattr(sys, "_MEIPASS")) / "client" / "style.qss"
            if frozen_path.exists():
                return frozen_path
        local_path = Path(__file__).with_name("style.qss")
        if local_path.exists():
            return local_path
    except Exception:
        pass
    return None


def run() -> None:
    # 可选读取外部 .env；不存在也不会报错
    try:
        load_dotenv()
    except Exception:
        pass

    api_base = os.environ.get("API_BASE", DEFAULT_API_BASE)
    ws_url = os.environ.get("WS_URL", DEFAULT_WS_URL)

    app = QtWidgets.QApplication(sys.argv)
    AsyncioRunner.instance().start()

    # 加载全局样式：优先外部文件，其次内置回退
    try:
        qss_path = _find_stylesheet_path()
        if qss_path is not None:
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        else:
            app.setStyleSheet(EMBEDDED_QSS)
    except Exception:
        try:
            app.setStyleSheet(EMBEDDED_QSS)
        except Exception:
            pass

    w = MainApp(api_base, ws_url)
    w.resize(600, 400)
    w.show()

    app.exec()
    AsyncioRunner.instance().stop()


if __name__ == "__main__":
    run()
