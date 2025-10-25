from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from .deps import get_current_user, get_db
from .models import Message, User


router = APIRouter()


active_connections: Dict[int, WebSocket] = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        # 第一条消息应包含 token，用于鉴权。格式：{"type":"auth","token":"..."}
        init = await websocket.receive_json()
        if init.get("type") != "auth":
            await websocket.close(code=4401)
            return
        token = init.get("token")
        # 复用 HTTP auth 依赖较复杂，这里直接解码。
        from .security import decode_access_token
        from sqlalchemy import select

        try:
            payload = decode_access_token(token)
            user_id = int(payload.get("sub"))
        except Exception:  # noqa: BLE001
            await websocket.close(code=4401)
            return
        user = db.get(User, user_id)
        if not user:
            await websocket.close(code=4401)
            return

        active_connections[user_id] = websocket
        await websocket.send_json({"type": "ready", "user_id": user_id})

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "send":
                to_user_id = int(data["to_user_id"])
                body = str(data["body"])
                message = Message(sender_id=user_id, receiver_id=to_user_id, body=body)
                db.add(message)
                db.commit()
                db.refresh(message)

                # 发给自己客户端确认
                await websocket.send_json(
                    {
                        "type": "sent",
                        "message": {
                            "id": message.id,
                            "sender_id": message.sender_id,
                            "receiver_id": message.receiver_id,
                            "body": message.body,
                            "created_at": message.created_at.isoformat(),
                        },
                    }
                )

                # 若对方在线，推送
                peer = active_connections.get(to_user_id)
                if peer is not None:
                    await peer.send_json(
                        {
                            "type": "recv",
                            "message": {
                                "id": message.id,
                                "sender_id": message.sender_id,
                                "receiver_id": message.receiver_id,
                                "body": message.body,
                                "created_at": message.created_at.isoformat(),
                            },
                        }
                    )
            else:
                await websocket.send_json(
                    {"type": "error", "detail": "Unknown message type"}
                )
    except WebSocketDisconnect:
        pass
    finally:
        # 清理连接
        to_remove = None
        for uid, ws in active_connections.items():
            if ws is websocket:
                to_remove = uid
                break
        if to_remove is not None:
            active_connections.pop(to_remove, None)
