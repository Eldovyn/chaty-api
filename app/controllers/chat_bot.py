from ..databases import ChatHistoryDatabase, RoomChatDatabase
from flask import jsonify
from ..utils import (
    Validation,
    GeminiAI,
    ImageKitImageGenerator,
)
from ..serializers import ChatHistorySerializer, RoomChatSerializer
import os
import datetime
from ..models import ChatRoomModel, ChatHistoryModel
import uuid
from .. import socket_io


def now_ts():
    return (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )


class ChatBotController:
    NAMESPACE = "/chat-bot"
    HISTORY_CAP = 2000

    def __init__(self):
        self.gemini = GeminiAI()
        self.chat_history_serializer = ChatHistorySerializer()
        self.room_chat_serializer = RoomChatSerializer()
        self.image_generator = ImageKitImageGenerator()

    async def get_all_rooms(self, user):
        if not (
            data_rooms := await RoomChatDatabase.get(
                "get_all_rooms_by_user_id", user_id=user.id
            )
        ):
            return jsonify({"message": "chat history not found"}), 404
        data_rooms_serialize = [
            self.room_chat_serializer.serialize(room) for room in data_rooms
        ]
        return (
            jsonify({"message": "success get all rooms", "data": data_rooms_serialize}),
            200,
        )

    async def get_messages(self, user, room_id):
        if not (
            data_user := ChatHistoryDatabase.get(
                "get_chat_history_by_user_id", user_id=user.id, room_id=room_id
            )
        ):
            return jsonify({"message": "chat history not found"}), 404

    async def create_message(self, user, text, room, docs):
        errors = {}
        await Validation.validate_required_text_async(errors, "text", text)
        if docs:
            docs = docs[0]
            _, ext = os.path.splitext(docs.filename)
            ext = ext.lower()
            if ext not in (".pdf", ".docx", ".txt"):
                errors["file"] = "IS_INVALID"
        if errors:
            return jsonify({"errors": errors, "message": "validation errors"}), 400
        if not room:
            room = f"room-{uuid.uuid4().hex}"

        user_room = ChatRoomModel.objects(room=room, user=user).first()
        if not user_room:
            user_room = ChatRoomModel(room=room, user=user)
            user_room.save()

        ts_user = now_ts()
        ChatHistoryModel(
            text=text,
            role="user",
            user=user,
            room=user_room,
            is_image=False,
            links=[],
        ).save()

        bot_result = self.gemini.handle_request(text, self.image_generator)
        bot_text = bot_result.get("content", "")
        is_image = bot_result.get("is_image", False)

        ts_assistant = now_ts()

        ChatHistoryModel(
            text=bot_text,
            role="assistant",
            user=user,
            room=user_room,
            is_image=is_image,
            links=[],
        ).save()

        histories = (
            ChatHistoryModel.objects(room=user_room, user=user).order_by("id").limit(10)
        )
        context_list = [f"{h.role}: {h.text}" for h in histories]

        if context_list:
            title_room = self.gemini.generate_title_from_context(context_list)
            user_room.title = title_room
            user_room.save()

        latest_rooms = ChatRoomModel.objects(user=user, deleted_at=None)

        room_items = [self.room_chat_serializer.serialize(r) for r in latest_rooms]
        room_items.reverse()
        socket_io.emit(
            "chat",
            {"type": "system_clear", "ts": now_ts()},
            to=room,
            namespace=self.NAMESPACE,
        )
        socket_io.emit(
            "chat",
            {
                "type": "user",
                "text": text,
                "ts": ts_user,
                "is_image": False,
            },
            to=room,
            namespace=self.NAMESPACE,
        )
        socket_io.emit(
            "chat",
            {
                "type": "assistant",
                "text": bot_text,
                "ts": ts_assistant,
                "is_image": is_image,
            },
            to=room,
            namespace=self.NAMESPACE,
        )
        socket_io.emit(
            "rooms_updated",
            {
                "rooms": room_items,
            },
            to=room,
            namespace=self.NAMESPACE,
        )

        return jsonify(
            {
                "message": "success create message",
                "data": [
                    {
                        "type": "user",
                        "text": text,
                        "ts": ts_user,
                        "is_image": False,
                    },
                    {
                        "type": "assistant",
                        "text": bot_text,
                        "ts": ts_assistant,
                        "is_image": is_image,
                    },
                ],
                "rooms_updated": room_items,
            }
        )
