from flask_socketio import emit, join_room
from flask import request
import datetime
from ..utils import GeminiAI


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    api_gemini = GeminiAI()
    DEFAULT_ROOM = "global"

    _HISTORY = []
    _HISTORY_CAP = 2000

    def _now_iso():
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _append(room: str, role: str, text: str):
        _HISTORY.append({"room": room, "role": role, "text": text, "ts": _now_iso()})
        if len(_HISTORY) > _HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - _HISTORY_CAP]

    def _history_for_room(room: str, limit: int = 200):
        items = [m for m in _HISTORY if m["room"] == room]
        return items[-limit:]

    @socketio.on("connect", namespace=NAMESPACE)
    def handle_connect():
        sid = request.sid
        room = DEFAULT_ROOM
        join_room(room, namespace=NAMESPACE)

        print(
            f"[connect] ns={NAMESPACE} sid={sid} room={room} ip={request.remote_addr}"
        )

        history = _history_for_room(room)
        if history:
            emit(
                "chat",
                {
                    "type": "history",
                    "items": history,
                    "ts": _now_iso(),
                },
                to=sid,
                namespace=NAMESPACE,
            )
        else:
            system_msg = {
                "type": "system",
                "text": f"Connected to {NAMESPACE}",
                "ts": _now_iso(),
            }
            emit("chat", system_msg, to=sid, namespace=NAMESPACE)
            _append(room, "system", system_msg["text"])

    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        room = (data or {}).get("room", DEFAULT_ROOM)
        text = (data or {}).get("text", "").strip()

        user_msg = {"type": "user", "text": text, "ts": _now_iso()}
        emit("chat", user_msg, to=room, namespace=NAMESPACE)
        _append(room, "user", text)

        bot_response = api_gemini.generate_sync(text)

        assistant_msg = {"type": "assistant", "text": bot_response, "ts": _now_iso()}
        emit("chat", assistant_msg, to=room, namespace=NAMESPACE)
        _append(room, "assistant", bot_response)
