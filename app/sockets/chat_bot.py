from flask_socketio import emit, join_room
from flask import request
import uuid
import datetime
from ..utils import GeminiAI


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    HISTORY_CAP = 2000

    api_gemini = GeminiAI()

    _HISTORY = []
    _ROOM_HAS_SYSTEM = set()
    _SID_ROOM = {}

    @socketio.on("connect", namespace=NAMESPACE)
    def handle_connect(auth=None):
        sid = request.sid

        # === inline _resolve_room_from_auth_or_args ===
        room = None

        if isinstance(auth, dict):
            room = (auth.get("room") or "").strip()

        if not room:
            room = (
                request.args.get("room") or request.args.get("room_id") or ""
            ).strip()

        if not room:
            # inline _generate_new_room_id
            room = f"room-{uuid.uuid4().hex}"
        # === end inline _resolve_room_from_auth_or_args ===

        join_room(room, sid=sid, namespace=NAMESPACE)
        _SID_ROOM[sid] = room

        print(
            f"[connect] ns={NAMESPACE} sid={sid} room={room} ip={request.remote_addr}"
        )

        # inline _now_iso
        now_ts = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        emit(
            "room_created",
            {"room": room, "ts": now_ts},
            to=sid,
            namespace=NAMESPACE,
        )

        # === inline _send_initial_message_or_history ===
        # inline _get_history_for_room(room)
        items = [m for m in _HISTORY if m["room"] == room and m.get("role") != "system"]
        history = items[-200:]

        if history:
            emit(
                "chat",
                {"type": "history", "items": history, "ts": now_ts},
                to=sid,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)
        else:
            now_ts2 = (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
            emit(
                "chat",
                {
                    "type": "system",
                    "text": "Belum ada pesan. Mulai ngobrol di bawah ✨",
                    "ts": now_ts2,
                },
                to=sid,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.add(room)
        # === end inline _send_initial_message_or_history ===

    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        _SID_ROOM.pop(sid, None)
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        sid = request.sid

        payload_room = (data or {}).get("room")

        # === inline _ensure_room_for_sid ===
        room = (payload_room or _SID_ROOM.get(sid) or "").strip()
        if not room:
            room = f"room-{uuid.uuid4().hex}"  # inline _generate_new_room_id
            _SID_ROOM[sid] = room
        # === end inline _ensure_room_for_sid ===

        text = (data or {}).get("text", "").strip()
        if not text:
            return

        join_room(room, sid=sid, namespace=NAMESPACE)

        # === inline _clear_system_message_if_needed ===
        if room in _ROOM_HAS_SYSTEM:
            now_ts_clear = (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
            emit(
                "chat",
                {"type": "system_clear", "ts": now_ts_clear},
                to=room,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)
        # === end inline _clear_system_message_if_needed ===

        # === inline _send_user_message + _append_message ===
        now_ts_user = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        user_message = {
            "type": "user",
            "text": text,
            "ts": now_ts_user,
            "room": room,
        }
        emit("chat", user_message, to=room, namespace=NAMESPACE)

        # _append_message(room, "user", text)
        _HISTORY.append({"room": room, "role": "user", "text": text, "ts": now_ts_user})
        if len(_HISTORY) > HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - HISTORY_CAP]
        # === end inline _send_user_message + _append_message ===

        # panggil LLM
        bot_response = api_gemini.generate_sync(text)

        # === inline _send_assistant_message + _append_message ===
        now_ts_assistant = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        assistant_message = {
            "type": "assistant",
            "text": bot_response,
            "ts": now_ts_assistant,
            "room": room,
        }
        emit("chat", assistant_message, to=room, namespace=NAMESPACE)

        _HISTORY.append(
            {
                "room": room,
                "role": "assistant",
                "text": bot_response,
                "ts": now_ts_assistant,
            }
        )
        if len(_HISTORY) > HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - HISTORY_CAP]
        # === end inline _send_assistant_message + _append_message ===
