from flask_socketio import emit, join_room, disconnect
from flask import request
import uuid
import datetime
from ..utils import GeminiAI, AuthJwt, ImageKitImageGenerator
from ..models import UserModel, BlacklistTokenModel, ChatHistoryModel, ChatRoomModel
from ..serializers import RoomChatSerializer
from .. import _HISTORY, _ROOM_HAS_SYSTEM, _SID_ROOM, _SID_USER


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    HISTORY_CAP = 2000

    api_gemini = GeminiAI()
    image_generator = ImageKitImageGenerator()
    room_chat_serializer = RoomChatSerializer()

    # ==============================================
    # CONNECT
    # ==============================================
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

        # Token timestamp check
        iat = payload.get("iat")
        issued_time = datetime.datetime.fromtimestamp(iat, tz=datetime.timezone.utc)
        ua = getattr(user, "updated_at", None)
        if ua is not None and ua.tzinfo is None:
            ua = ua.replace(tzinfo=datetime.timezone.utc)

        SKEW = datetime.timedelta(seconds=60)
        if ua and (issued_time + SKEW) < ua:
            disconnect(sid=sid)
            return

        # Blacklist check
        jti = payload.get("jti")
        if jti and BlacklistTokenModel.objects(jti=jti).first():
            disconnect(sid=sid)
            return

        if not user.is_active:
            disconnect(sid=sid)
            return

        # Mapping SID ke User
        _SID_USER[sid] = user

        # Tentukan room
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
            to=room,
            namespace=NAMESPACE,
        )

        user_room = ChatRoomModel.objects(room=room, user=user).first()

        # ===============================
        # LOAD HISTORY (MODEL BARU)
        # ===============================
        history_items = []
        if user_room is not None:
            user_chat_histories = (
                ChatHistoryModel.objects(room=user_room, user=user)
                .order_by("id")
                .limit(200)
            )

            for ch in user_chat_histories:
                try:
                    created_at = ch.id.generation_time.replace(
                        tzinfo=datetime.timezone.utc
                    )
                except Exception:
                    created_at = datetime.datetime.now(datetime.timezone.utc)

                ts_iso = created_at.isoformat().replace("+00:00", "Z")

                history_items.append(
                    {
                        "room": room,
                        "role": ch.role,
                        "text": ch.text,
                        "ts": ts_iso,
                        "is_image": getattr(ch, "is_image", False),
                    }
                )

            history_items = history_items[-200:]

        if history_items:
            emit(
                "chat",
                {"type": "history", "items": history_items, "ts": now_ts},
                to=room,
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
                to=room,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.add(room)

    # ==============================================
    # DISCONNECT
    # ==============================================
    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        _SID_ROOM.pop(sid, None)
        _SID_USER.pop(sid, None)
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    # ==============================================
    # CHAT MESSAGE
    # ==============================================
    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        sid = request.sid

        payload_room = (data or {}).get("room")
        room = (payload_room or _SID_ROOM.get(sid) or "").strip()
        if not room:
            room = f"room-{uuid.uuid4().hex}"
            _SID_ROOM[sid] = room

        text = (data or {}).get("text", "").strip()
        file = (data or {}).get("file")  # Not used yet
        if not text:
            return

        join_room(room, sid=sid, namespace=NAMESPACE)

        # Clear system text if existed
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

        # ===============================
        # Broadcast USER message
        # ===============================
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

        # ===============================
        # AI RESPONSE
        # ===============================
        bot_result = api_gemini.handle_request(text, image_generator)
        bot_text = bot_result.get("content", "")
        is_image = bot_result.get("is_image", False)

        now_ts_assistant = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        assistant_message = {
            "type": "assistant",
            "text": bot_text,
            "ts": now_ts_assistant,
            "room": room,
            "is_image": is_image,
        }
        emit("chat", assistant_message, to=room, namespace=NAMESPACE)

        _HISTORY.append(
            {
                "room": room,
                "role": "assistant",
                "text": bot_text,
                "ts": now_ts_assistant,
                "is_image": is_image,
            }
        )
        if len(_HISTORY) > HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - HISTORY_CAP]

        # ===============================
        # SAVE TO DATABASE (MODEL BARU)
        # ===============================
        user = _SID_USER.get(sid)
        if user is not None:
            user_room = ChatRoomModel.objects(room=room, user=user).first()

            if not user_room:
                user_room = ChatRoomModel(room=room, user=user)
                user_room.save()

            # Save USER message
            ChatHistoryModel(
                text=text,
                role="user",
                user=user,
                room=user_room,
                is_image=False,
                links=[],
            ).save()

            # Save ASSISTANT message
            ChatHistoryModel(
                text=bot_text,
                role="assistant",
                user=user,
                room=user_room,
                is_image=is_image,
                links=[],
            ).save()

            # ===============================
            # GENERATE TITLE (MODEL BARU)
            # ===============================
            histories = (
                ChatHistoryModel.objects(room=user_room, user=user)
                .order_by("id")
                .limit(10)
            )

            context_list = []
            for h in histories:
                context_list.append(f"{h.role}: {h.text}")

            if context_list:
                title_room = api_gemini.generate_title_from_context(context_list)
                user_room.title = title_room
                user_room.save()

            # ===============================
            # UPDATE ROOM LIST
            # ===============================
            latest_rooms = ChatRoomModel.objects(user=user, deleted_at=None)

            room_items = []
            for r in latest_rooms:
                room_items.append(room_chat_serializer.serialize(r))

            room_items.reverse()

            emit(
                "rooms_updated",
                {"rooms": room_items},
                to=room,
                namespace=NAMESPACE,
            )
