from ..databases import ChatHistoryDatabase, RoomChatDatabase
from flask import jsonify
from ..utils import (
    Validation,
    GeminiAI,
)
import uuid
from ..serializers import ChatHistorySerializer, RoomChatSerializer
import google.genai.errors


class ChatRoomController:
    def __init__(self):
        self.room_chat_serializer = RoomChatSerializer()

    async def delete_room(self, user, room):
        if not (
            data_room := await RoomChatDatabase.delete(
                "delete_room_by_user_id", user_id=f"{user.id}", room=f"{room}"
            )
        ):
            return jsonify({"message": "chat room not found"}), 404
        return jsonify({"message": "successfully delete chat room"}), 201

    async def get_all_rooms(self, user):
        if not (
            data_rooms := await RoomChatDatabase.get(
                "get_all_rooms_by_user_id", user_id=user.id
            )
        ):
            return jsonify({"message": "chat rooms not found"}), 404
        data_rooms_serialize = [
            self.room_chat_serializer.serialize(room) for room in data_rooms
        ]
        return (
            jsonify({"message": "success get all rooms", "data": data_rooms_serialize}),
            200,
        )

    async def clear_rooms(self, user):
        if not (
            data_rooms := await RoomChatDatabase.get(
                "get_all_rooms_by_user_id", user_id=user.id
            )
        ):
            return jsonify({"message": "chat rooms not found"}), 404
        await RoomChatDatabase.delete(
            "delete_all_rooms_by_user_id", user_id=f"{user.id}"
        )
        return jsonify({"message": "successfully clear all chat rooms"}), 201
