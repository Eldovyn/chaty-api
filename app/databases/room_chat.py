from .database import Database
from ..models import UserModel, ChatRoomModel


class RoomChatDatabase(Database):
    @staticmethod
    async def insert():
        pass

    @staticmethod
    async def get(category, **kwargs):
        user_id = kwargs.get("user_id")
        if category == "get_all_rooms_by_user_id":
            if user_data := UserModel.objects(id=user_id).first():
                if user_rooms := ChatRoomModel.objects(user=user_data).all():
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
        pass

    @staticmethod
    async def update(category, **kwargs):
        pass

    @staticmethod
    def update_sync(category, **kwargs):
        pass
