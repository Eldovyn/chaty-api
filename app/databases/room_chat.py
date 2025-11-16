from .database import Database
from ..models import UserModel, ChatRoomModel, ChatHistoryModel


class RoomChatDatabase(Database):
    @staticmethod
    async def insert():
        pass

    @staticmethod
    def insert_sync(user_id, room_id, original_message, response_message):
        if user_data := UserModel.objects(id=user_id).first():
            if user_room := ChatRoomModel.objects(id=room_id).first():
                user_chat = ChatHistoryModel(
                    original_message=original_message,
                    response_message=response_message,
                    user=user_data,
                    room=user_room,
                )
                user_chat.save()
            else:
                user_room = ChatRoomModel(user=user_data)
                user_room.save()
                user_room.title = f"Room {user_room.id}"
                user_room.save()
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
        if category == "get_all_rooms_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                if user_rooms := ChatRoomModel.objects(user=user_data).order_by(
                    "-created_at"
                ):
                    return user_rooms

    @staticmethod
    def get_sync(category, **kwargs):
        user_id = kwargs.get("user_id")
        room_id = kwargs.get("room_id")
        if category == "get_room_by_room_id":
            if user_data := UserModel.objects(id=user_id).first():
                if room_data := ChatRoomModel.objects(
                    id=room_id, user=user_data
                ).first():
                    return room_data

    @staticmethod
    async def delete(category, **kwargs):
        user_id = kwargs.get("user_id")
        if category == "delete_all_rooms_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                if user_rooms := ChatRoomModel.objects(user=user_data):
                    user_rooms.delete()
                    return user_rooms

    @staticmethod
    async def update(category, **kwargs):
        pass

    @staticmethod
    def update_sync(category, **kwargs):
        pass
