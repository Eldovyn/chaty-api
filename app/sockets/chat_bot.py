from flask_socketio import send, emit, disconnect
from flask import request
from ..utils import (
    AuthJwt,
)
from ..models import UserModel, BlacklistTokenModel
import datetime
from databases import ChatHistoryDatabase, RoomChatDatabase
from serializers import ChatHistorySerializer


def register_chat_bot_socketio_events(socketio):
    chat_history_serializer = ChatHistorySerializer()

    @socketio.on("connect", namespace="/chat-bot")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socketio.on("disconnect", namespace="/chat-bot")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socketio.on("join", namespace="/chat-bot")
    def handle_join(data):
        token = request.headers.get(
            "Authorization",
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTAxZDhlN2JmOWJkYTAzNWFmMzIyNWMiLCJpYXQiOjE3NjIxNDA0OTJ9.uh1AaMmfa9QJy1wuRTL6hnMbhML6wAmSUk8P-8AECeuC1EEmjzBdqI1t1eB3jWEF6vbn-o4V9hEtsFqXRa2Q8fz_Ysg3OQ57U2T_cIqtjOTHxVuBhOV6niu484oSjPLaHlUbH1mjAzVUxDlOK2oya44UPKViG5ixG0Ka0UbYAYpdqmWFJMIaDyaRvaGgR8JscI_Ciw0qFk9xeGb9Z_vda4bWwB1HrDvMKkM0_QDVCZMUhgUAYH_VqFII61Zcp-sSXgLBwMT7doTnNJjMY5xcn2yD3BiqGSfBLM6kxMYRyeU-0_RhZ1rtSlJeCaQN9BmA7VDu0WBAHjOgckjZpT8a1A",
        )
        room_id = data.get("room_id")
        if not token:
            disconnect()
            return

        payload = AuthJwt.verify_token_sync(token)
        if not payload:
            disconnect()
            return

        user_id = payload.get("sub")
        if not user_id:
            disconnect()
            return

        user = UserModel.objects(id=user_id).first()
        if not user:
            disconnect()
            return

        iat = payload.get("iat")
        issued_time = datetime.datetime.fromtimestamp(iat, tz=datetime.timezone.utc)
        ua = user.updated_at
        if ua.tzinfo is None:
            ua = ua.replace(tzinfo=datetime.timezone.utc)

        SKEW = datetime.timedelta(seconds=60)
        if ua and (issued_time + SKEW) < ua:
            disconnect()
            return

        jti = payload.get("jti")
        if jti and BlacklistTokenModel.objects(jti=jti).first():
            disconnect()
            return

        if not user.is_active:
            disconnect()
            return

        if not (
            room_data := RoomChatDatabase.get_sync(
                "get_room_by_room_id", room_id=room_id, user_id=user_id
            )
        ):
            room_id = None

        chat_list = []
        if room_id:
            if chat_history := ChatHistoryDatabase.get_sync(
                "get_chat_history_by_user_id", room_id=room_id, user_id=user_id
            ):
                for chat in chat_history:
                    chat_list.append(chat_history_serializer.serialize(chat))

            send(f"{user.username} joined the room.", to=room_id)
            emit("chat:history", chat_list, to=room_id)
