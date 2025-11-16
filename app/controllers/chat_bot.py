from ..databases import ChatHistoryDatabase, RoomChatDatabase
from flask import jsonify
from werkzeug.utils import secure_filename
from ..utils import (
    Validation,
    GeminiAI,
    ImageKitImageGenerator,
)
from .. import socket_io
from ..serializers import ChatHistorySerializer, RoomChatSerializer
import os
import datetime
from ..models import ChatRoomModel, ChatHistoryModel


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
        await Validation.validate_required_text_async(errors, "room", room)
        if docs:
            docs = docs[0]
            _, ext = os.path.splitext(docs.filename)
            ext = ext.lower()
            if ext not in (".pdf", ".docx", ".txt"):
                errors["file"] = "IS_INVALID"
        if errors:
            return jsonify({"errors": errors, "message": "validation errors"}), 400
        now_ts = (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        user_message = {
            "type": "user",
            "text": text,
            "ts": now_ts,
            "room": room,
        }
        bot_result = self.gemini.handle_request(text, self.image_generator)
        bot_text = bot_result.get("content", "")
        is_image = bot_result.get("is_image", False)
        user_room = ChatRoomModel.objects(room=room, user=user).first()
        if not user_room:
            user_room = ChatRoomModel(room=room, user=user)
            user_room.save()
        room_items = ChatRoomModel.objects(user=user).order_by("-updated_at")
        result = []
        for r in room_items:
            _result = self.room_chat_serializer.serialize(r)
            result.append(_result)

        ChatHistoryModel(
            original_message=text,
            response_message=bot_text,
            links=[],
            role="user",
            user=user,
            room=user_room,
            is_image=is_image,
        ).save()

        history_items = (
            ChatHistoryModel.objects(room=user_room, user=user)
            .all()
            .order_by("-created_at")[:50]
        )

        socket_io.emit(
            "chat",
            {"type": "history", "items": history_items, "ts": now_ts},
            to=room,
            namespace=self.NAMESPACE,
        )
        socket_io.emit(
            "rooms_updated",
            {"rooms": result},
            to=room,
            namespace=self.NAMESPACE,
        )

        return jsonify({"status": "ok"}), 201
