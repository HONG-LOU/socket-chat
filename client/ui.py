import os
from typing import Any, Dict, Optional

from PyQt6 import QtCore, QtWidgets

from .api import ApiClient
from .ws import WSClient
from .async_runner import AsyncioRunner


SHOW_MSG = os.environ.get("CLIENT_SHOW_MESSAGES", "1").lower() not in (
    "0",
    "false",
    "no",
    "off",
)
CLEAR_MS = int(os.environ.get("CLIENT_MSG_DURATION_MS", "3000"))


def flash_label(label: QtWidgets.QLabel, text: str) -> None:
    if not SHOW_MSG:
        return
    label.setText(text)
    label.show()
    QtCore.QTimer.singleShot(CLEAR_MS, lambda: (label.clear(), label.hide()))


def friendly_error(ex: Exception) -> str:
    msg = str(ex)
    # 常见错误翻译
    translations = [
        ("401 Unauthorized", "未登录或登录已过期"),
        ("Email already registered", "该邮箱已注册"),
        ("Invalid credentials", "邮箱或密码错误"),
        ("Friend not found", "未找到该用户"),
        ("Already friends", "已是好友"),
        ("Cannot add self", "不能添加自己为好友"),
        ("403 Forbidden", "无权限执行该操作"),
        ("404", "未找到资源"),
        ("timeout", "网络超时，请稍后重试"),
        ("Connection refused", "服务器不可用，请稍后再试"),
    ]
    low = msg.lower()
    for key, zh in translations:
        if key.lower() in low:
            return zh
    # httpx HTTPError 常见格式
    if "Client error" in msg or "Server error" in msg:
        return "请求失败，请稍后重试"
    return "操作失败，请稍后重试"


class LoginWindow(QtWidgets.QWidget):
    logged_in = QtCore.pyqtSignal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.setWindowTitle("登录 / 注册")

        self.email = QtWidgets.QLineEdit()
        self.email.setPlaceholderText("邮箱")
        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.display_name = QtWidgets.QLineEdit()
        self.display_name.setPlaceholderText("昵称（注册用）")

        btn_login = QtWidgets.QPushButton("登录")
        btn_register = QtWidgets.QPushButton("注册")
        self.msg = QtWidgets.QLabel()
        if not SHOW_MSG:
            self.msg.hide()

        form = QtWidgets.QFormLayout()
        form.addRow("邮箱", self.email)
        form.addRow("密码", self.password)
        form.addRow("昵称", self.display_name)
        actions = QtWidgets.QHBoxLayout()
        actions.addWidget(btn_login)
        actions.addWidget(btn_register)
        form.addRow(actions)
        form.addRow(self.msg)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        card.setLayout(form)

        layout = QtWidgets.QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(card)
        layout.addStretch(1)
        layout.setContentsMargins(80, 40, 80, 40)
        self.setLayout(layout)

        btn_login.clicked.connect(self.on_login)
        btn_register.clicked.connect(self.on_register)

    def on_login(self) -> None:
        try:
            token = self.api.login(self.email.text(), self.password.text())
            me = self.api.me()
            self.logged_in.emit({"token": token, "me": me})
        except Exception as e:  # noqa: BLE001
            flash_label(self.msg, f"登录失败: {friendly_error(e)}")

    def on_register(self) -> None:
        try:
            self.api.register(
                self.email.text(), self.password.text(), self.display_name.text()
            )
            flash_label(self.msg, "注册成功，请登录")
        except Exception as e:  # noqa: BLE001
            flash_label(self.msg, f"注册失败: {friendly_error(e)}")


class FriendsWindow(QtWidgets.QWidget):
    open_chat = QtCore.pyqtSignal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.setWindowTitle("好友列表")

        self.list = QtWidgets.QListWidget()
        self.list.setObjectName("FriendsList")
        self.list.setUniformItemSizes(True)
        self.list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.list.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.add_email = QtWidgets.QLineEdit()
        self.add_email.setPlaceholderText("好友邮箱")
        btn_add = QtWidgets.QPushButton("添加")
        btn_refresh = QtWidgets.QPushButton("刷新")
        self.msg = QtWidgets.QLabel()
        if not SHOW_MSG:
            self.msg.hide()

        top_bar = QtWidgets.QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QtWidgets.QHBoxLayout(top_bar)
        title = QtWidgets.QLabel("好友")
        title.setObjectName("Title")
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        top_layout.addWidget(self.add_email)
        top_layout.addWidget(btn_add)
        top_layout.addWidget(btn_refresh)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(top_bar)
        layout.addWidget(self.list)
        layout.addWidget(self.msg)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)

        btn_add.clicked.connect(self.on_add)
        btn_refresh.clicked.connect(self.refresh)
        self.list.itemDoubleClicked.connect(self.on_open_chat)

        self.refresh()

    def refresh(self) -> None:
        try:
            self.list.clear()
            for f in self.api.friends():
                item = QtWidgets.QListWidgetItem(f["display_name"])  # 仅显示昵称
                item.setData(QtCore.Qt.ItemDataRole.UserRole, f)
                self.list.addItem(item)
        except Exception as e:  # noqa: BLE001
            flash_label(self.msg, f"加载失败: {friendly_error(e)}")

    def on_add(self) -> None:
        try:
            f = self.api.add_friend(self.add_email.text())
            flash_label(self.msg, f"已添加: {f['display_name']}")
            self.refresh()
        except Exception as e:  # noqa: BLE001
            flash_label(self.msg, f"添加失败: {friendly_error(e)}")

    def on_open_chat(self, item: QtWidgets.QListWidgetItem) -> None:  # type: ignore[name-defined]
        data = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self.open_chat.emit(data)


class ChatWindow(QtWidgets.QWidget):
    message_received = QtCore.pyqtSignal(dict)

    def __init__(
        self, api: ApiClient, ws: WSClient, me: Dict[str, Any], peer: Dict[str, Any]
    ):
        super().__init__()
        self.api = api
        self.ws = ws
        self.me = me
        self.peer = peer
        self.setWindowTitle(f"与 {peer['display_name']} 聊天")
        self.resize(900, 620)
        self.setMinimumSize(720, 520)

        self.history = QtWidgets.QScrollArea()
        self.history.setWidgetResizable(True)
        self.scroll_body = QtWidgets.QWidget()
        self.scroll_body.setObjectName("ChatArea")
        self.messages_layout = QtWidgets.QVBoxLayout(self.scroll_body)
        # 底部锚点用于自动滚动
        self.bottom_anchor = QtWidgets.QWidget()
        self.bottom_anchor.setFixedHeight(1)
        self.messages_layout.addWidget(self.bottom_anchor)
        self.history.setWidget(self.scroll_body)
        self.input = QtWidgets.QLineEdit()
        self.input.returnPressed.connect(self.on_send)
        btn_send = QtWidgets.QPushButton("发送")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.history)
        bottom = QtWidgets.QHBoxLayout()
        bottom.addWidget(self.input)
        bottom.addWidget(btn_send)
        layout.addLayout(bottom)
        self.setLayout(layout)

        btn_send.clicked.connect(self.on_send)

        # 主线程安全更新
        self.message_received.connect(self.append_message)

        # 内容变化后自动滚动到底部
        try:
            self.history.verticalScrollBar().rangeChanged.connect(
                lambda _min, _max: self.scroll_to_bottom()
            )
        except Exception:
            pass

        # 加载历史
        for m in self.api.history(self.peer["id"]):
            self.append_message(m)

        # 订阅 WS 收到的消息（同时处理 sent 与 recv）
        def on_recv(data: Dict[str, Any]) -> None:
            if data.get("type") in ("recv", "sent"):
                m = data.get("message")
                if m and (
                    (
                        m["sender_id"] == self.peer["id"]
                        and m["receiver_id"] == self.me["id"]
                    )
                    or (
                        m["sender_id"] == self.me["id"]
                        and m["receiver_id"] == self.peer["id"]
                    )
                ):
                    self.message_received.emit(m)

        self.ws.on_received = on_recv

    def append_message(self, m: Dict[str, Any]) -> None:
        me_side = m["sender_id"] == self.me["id"]
        bubble = QtWidgets.QFrame()
        bubble.setObjectName("BubbleMe" if me_side else "BubblePeer")
        text = QtWidgets.QLabel(m["body"])
        text.setWordWrap(True)
        bl = QtWidgets.QHBoxLayout(bubble)
        bl.setContentsMargins(10, 8, 10, 8)
        bl.addWidget(text)

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if me_side:
            row.addStretch(1)
            row.addWidget(bubble, 0)
        else:
            row.addWidget(bubble, 0)
            row.addStretch(1)

        # 插入到锚点之前并滚动到底部
        idx = self.messages_layout.indexOf(self.bottom_anchor)
        if idx == -1:
            idx = self.messages_layout.count()
        self.messages_layout.insertLayout(idx, row)
        QtCore.QTimer.singleShot(0, self.scroll_to_bottom)

    def scroll_to_bottom(self) -> None:
        try:
            # 优先确保锚点可见
            self.history.ensureWidgetVisible(self.bottom_anchor, 0, 0)
        except Exception:
            pass
        try:
            # 同时设置滚动条到最大，双保险
            sb = self.history.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception:
            pass

    def on_send(self) -> None:
        body = self.input.text()
        self.input.clear()
        AsyncioRunner.instance().create_task(
            self.ws.send_message(self.peer["id"], body)
        )


class MainApp(QtWidgets.QStackedWidget):
    def __init__(self, api_base: str, ws_url: str):
        super().__init__()
        self.api = ApiClient(api_base)
        self.ws = WSClient(ws_url)

        self.login = LoginWindow(self.api)
        self.friends = FriendsWindow(self.api)
        self.addWidget(self.login)
        self.addWidget(self.friends)
        self.setCurrentWidget(self.login)

        self.login.logged_in.connect(self.on_logged_in)
        self.friends.open_chat.connect(self.on_open_chat)

    def on_logged_in(self, payload: Dict[str, Any]) -> None:
        token = payload["token"]
        me = payload["me"]
        self.ws.set_token(token)
        AsyncioRunner.instance().create_task(self.ws.connect())
        self.setCurrentWidget(self.friends)
        self.me = me  # type: ignore[attr-defined]
        # 登录后自动刷新好友列表
        try:
            self.friends.refresh()
        except Exception:
            pass

    def on_open_chat(self, peer: Dict[str, Any]) -> None:
        w = ChatWindow(self.api, self.ws, self.me, peer)  # type: ignore[attr-defined]
        w.show()
