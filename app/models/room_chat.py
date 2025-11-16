import mongoengine as me
from .user import UserModel
from .base import BaseDocument


class ChatRoomModel(BaseDocument):
    title = me.StringField(required=False)
    room = me.StringField(required=True, unique=True)

    user = me.ReferenceField(UserModel, reverse_delete_rule=me.CASCADE)

    meta = {"collection": "chat_room"}
