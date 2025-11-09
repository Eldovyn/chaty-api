from .database import Database
from ..models import UserModel, ChatHistoryModel, ChatRoomModel


class ChatHistoryDatabase(Database):
    @staticmethod
    async def insert(user_id, original_message, response_message, room_id=None):
        if user_data := UserModel.objects(id=user_id).first():
            if not room_id:
                user_room = ChatRoomModel(user=user_data)
                user_room.save()
                user_room.title = f"Room {user_room.id}"
                user_room.save()
            else:
                user_room = ChatRoomModel.objects(id=room_id).first()
            if user_room:
                user_chat = ChatHistoryModel(
                    original_message=original_message,
                    response_message=response_message,
                    user=user_data,
                    room=user_room,
                )
                user_chat.save()
                return user_chat

    @staticmethod
    async def get(category, **kwargs):
        user_id = kwargs.get("user_id")
        room_id = kwargs.get("room_id")
        if category == "get_chat_history_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                return ChatHistoryModel.objects(user=user_data, room_id=room_id).all()
        if category == "get_all_rooms_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                if user_room := ChatRoomModel.objects(user=user_data).all():
                    return user_room

    @staticmethod
    def get_sync(category, **kwargs):
        user_id = kwargs.get("user_id")
        room_id = kwargs.get("room_id")
        if category == "get_chat_history_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                return ChatHistoryModel.objects(user=user_data, room_id=room_id).all()

    @staticmethod
    async def delete(category, **kwargs):
        pass

    @staticmethod
    async def update(category, **kwargs):
        pass

    @staticmethod
    def update_sync(category, **kwargs):
        pass
