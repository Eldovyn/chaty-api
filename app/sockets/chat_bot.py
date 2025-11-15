from flask_socketio import emit, join_room, disconnect
from flask import request
import uuid
import datetime
from ..utils import GeminiAI, AuthJwt
from ..models import UserModel, BlacklistTokenModel, ChatHistoryModel, ChatRoomModel


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    HISTORY_CAP = 2000

    api_gemini = GeminiAI()

    _HISTORY = []
    _ROOM_HAS_SYSTEM = set()
    _SID_ROOM = {}
    _SID_USER = {}

    @socketio.on("connect", namespace=NAMESPACE)
    def handle_connect(auth=None):
        sid = request.sid

        auth_data = auth if isinstance(auth, dict) else {}
        token = auth_data.get("token")
        room = auth_data.get("room")

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
        ua = getattr(user, "updated_at", None)
        if ua is not None and ua.tzinfo is None:
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

        _SID_USER[sid] = user

        if not room:
            room = f"room-{uuid.uuid4().hex}"

        join_room(room, sid=sid, namespace=NAMESPACE)
        _SID_ROOM[sid] = room

        print(
            f"[connect] ns={NAMESPACE} sid={sid} room={room} ip={request.remote_addr}"
        )

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

        user_room = ChatRoomModel.objects(title=room, user=user).first()
        if not user_room:
            user_room = ChatRoomModel(title=room, user=user)
            user_room.save()

        user_chat_histories = (
            ChatHistoryModel.objects(room=user_room, user=user)
            .order_by("id")
            .limit(200)
        )

        history_items = []
        for ch in user_chat_histories:
            try:
                created_at = ch.id.generation_time.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                created_at = datetime.datetime.now(datetime.timezone.utc)

            ts_iso = created_at.isoformat().replace("+00:00", "Z")

            history_items.append(
                {
                    "room": room,
                    "role": "user",
                    "text": ch.original_message,
                    "ts": ts_iso,
                }
            )
            history_items.append(
                {
                    "room": room,
                    "role": "assistant",
                    "text": ch.response_message,
                    "ts": ts_iso,
                }
            )

        history_items = history_items[-200:]

        if history_items:
            emit(
                "chat",
                {"type": "history", "items": history_items, "ts": now_ts},
                to=sid,
                namespace=NAMESPACE,
            )
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

    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        _SID_ROOM.pop(sid, None)
        _SID_USER.pop(sid, None)
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        sid = request.sid

        payload_room = (data or {}).get("room")

        room = (payload_room or _SID_ROOM.get(sid) or "").strip()
        if not room:
            room = f"room-{uuid.uuid4().hex}"
            _SID_ROOM[sid] = room

        text = (data or {}).get("text", "").strip()
        if not text:
            return

        join_room(room, sid=sid, namespace=NAMESPACE)

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

        _HISTORY.append({"room": room, "role": "user", "text": text, "ts": now_ts_user})
        if len(_HISTORY) > HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - HISTORY_CAP]

        # panggil LLM
        bot_response = api_gemini.generate_sync(text)

        # === kirim pesan assistant + simpan di in-memory history ===
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

        # ====== simpan ke DB (ChatHistoryModel) ======
        user = _SID_USER.get(sid)

        if user is not None:
            user_room = ChatRoomModel.objects(title=room, user=user).first()
            if not user_room:
                user_room = ChatRoomModel(title=room, user=user)
                user_room.save()

            ChatHistoryModel(
                original_message=text,
                response_message=bot_response,
                links=[],
                role="assistant",
                user=user,
                room=user_room,
            ).save()
