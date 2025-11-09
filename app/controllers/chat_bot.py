from ..databases import ChatHistoryDatabase, RoomChatDatabase
from flask import jsonify
from ..utils import (
    Validation,
    GeminiAI,
)
import uuid
from ..serializers import ChatHistorySerializer, RoomChatSerializer
import google.genai.errors


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

    async def create_message(self, user, original_message, room_id=None):
        errors = {}
        await Validation.validate_required_text_async(
            errors, "original_message", original_message
        )
        if errors:
            return jsonify({"errors": errors, "message": "validation errors"}), 400
        try:
            chat_gemini = await self.gemini.generate_async(original_message)
        except google.genai.errors.ServerError:
            return jsonify({"message": "service unavailable"}), 503
        if not room_id:
            user_chat = await ChatHistoryDatabase.insert(
                f"{user.id}", original_message, chat_gemini
            )
        else:
            user_chat = await ChatHistoryDatabase.insert(
                f"{user.id}",
                original_message,
                chat_gemini,
                room_id=room_id,
            )
        user_chat_serialize = self.chat_history_serializer.serialize(user_chat)
        return (
            jsonify({"message": "success create message", "data": user_chat_serialize}),
            201,
        )
