from flask_socketio import emit, join_room, disconnect
from flask import request
import uuid
import datetime
from ..utils import GeminiAI, AuthJwt
from ..models import UserModel, BlacklistTokenModel, ChatRoomModel, ChatHistoryModel


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    HISTORY_CAP = 2000

    api_gemini = GeminiAI()

    _HISTORY = []

    _ROOM_HAS_SYSTEM = set()

    _SID_ROOM = {}

    def _now_iso() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _append_message(room: str, role: str, text: str) -> None:
        if role == "system":
            return

        _HISTORY.append({"room": room, "role": role, "text": text, "ts": _now_iso()})

        if len(_HISTORY) > HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - HISTORY_CAP]

    def _get_history_for_room(room: str, limit: int = 200):
        items = [m for m in _HISTORY if m["room"] == room and m.get("role") != "system"]
        return items[-limit:]

    def _generate_new_room_id() -> str:
        return f"room-{uuid.uuid4().hex}"

    def _ensure_room_for_sid(sid: str, payload_room: str | None) -> str:
        room = (payload_room or _SID_ROOM.get(sid) or "").strip()
        if not room:
            room = _generate_new_room_id()
            _SID_ROOM[sid] = room
        return room

    def _send_initial_message_or_history(sid: str, room: str) -> None:
        history = _get_history_for_room(room)
        if history:
            emit(
                "chat",
                {"type": "history", "items": history, "ts": _now_iso()},
                to=sid,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)
        else:
            emit(
                "chat",
                {
                    "type": "system",
                    "text": "Belum ada pesan. Mulai ngobrol di bawah ✨",
                    "ts": _now_iso(),
                },
                to=sid,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.add(room)

    def _send_user_message(room: str, text: str) -> None:
        message = {
            "type": "user",
            "text": text,
            "ts": _now_iso(),
            "room": room,
        }
        emit("chat", message, to=room, namespace=NAMESPACE)
        _append_message(room, "user", text)

    def _send_assistant_message(room: str, text: str) -> None:
        message = {
            "type": "assistant",
            "text": text,
            "ts": _now_iso(),
            "room": room,
        }
        emit("chat", message, to=room, namespace=NAMESPACE)
        _append_message(room, "assistant", text)

    def _clear_system_message_if_needed(room: str) -> None:
        if room in _ROOM_HAS_SYSTEM:
            emit(
                "chat",
                {"type": "system_clear", "ts": _now_iso()},
                to=room,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)

    @socketio.on("connect", namespace=NAMESPACE)
    def handle_connect(auth):
        sid = request.sid
        token = auth.get("token")
        room = auth.get("room")
        if not token:
            disconnect(sid=sid)
            return

        payload = AuthJwt.verify_token_sync(token)
        if payload is None:
            disconnect(sid=sid)
            return

        user_id = payload.get("sub")
        if not user_id:
            disconnect(sid=sid)
            return

        user = UserModel.objects(id=user_id).first()
        if not user:
            disconnect(sid=sid)
            return

        iat = payload.get("iat")
        issued_time = datetime.datetime.fromtimestamp(iat, tz=datetime.timezone.utc)
        ua = user.updated_at
        if ua.tzinfo is None:
            ua = ua.replace(tzinfo=datetime.timezone.utc)

        SKEW = datetime.timedelta(seconds=60)
        if ua and (issued_time + SKEW) < ua:
            disconnect(sid=sid)
            return

        jti = payload.get("jti")
        if jti and BlacklistTokenModel.objects(jti=jti).first():
            disconnect(sid=sid)
            return

        if not user.is_active:
            disconnect(sid=sid)
            return

        if not room:
            room = _generate_new_room_id()

        join_room(room, sid=sid, namespace=NAMESPACE)
        _SID_ROOM[sid] = room

        print(
            f"[connect] ns={NAMESPACE} sid={sid} room={room} ip={request.remote_addr}"
        )

        emit(
            "room_created",
            {"room": room, "ts": _now_iso()},
            to=sid,
            namespace=NAMESPACE,
        )

        # _send_initial_message_or_history(sid, room)
        items = []
        if not (user_room := ChatRoomModel.objects(title=room, user=user).first()):
            

    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        _SID_ROOM.pop(sid, None)
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        sid = request.sid

        payload_room = (data or {}).get("room")
        room = _ensure_room_for_sid(sid, payload_room)

        text = (data or {}).get("text", "").strip()
        if not text:
            return

        join_room(room, sid=sid, namespace=NAMESPACE)

        _clear_system_message_if_needed(room)

        _send_user_message(room, text)

        bot_response = api_gemini.generate_sync(text)

        _send_assistant_message(room, bot_response)
