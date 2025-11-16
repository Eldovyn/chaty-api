from ..databases import ChatHistoryDatabase, RoomChatDatabase
from flask import jsonify
from werkzeug.utils import secure_filename
from ..utils import (
    Validation,
    GeminiAI,
)
import uuid
from .. import socket_io
from ..serializers import ChatHistorySerializer, RoomChatSerializer
import google.genai.errors
import os


class ChatBotController:
    def __init__(self):
        self.gemini = GeminiAI()
        self.chat_history_serializer = ChatHistorySerializer()
        self.room_chat_serializer = RoomChatSerializer()

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
        if not docs:
            errors["file"] = "IS_REQUIRED"
        else:
            docs = docs[0]
            _, ext = os.path.splitext(docs.filename)
            ext = ext.lower()
            if ext not in (".pdf", ".docx", ".txt"):
                errors["file"] = "IS_INVALID"
        if errors:
            return jsonify({"errors": errors, "message": "validation errors"}), 400
