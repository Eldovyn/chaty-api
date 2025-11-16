import mongoengine as me
from .user import UserModel
from .room_chat import ChatRoomModel
from .base import BaseDocument


class ChatHistoryModel(BaseDocument):
    original_message = me.StringField(required=True)
    response_message = me.StringField(required=True)
    links = me.ListField(me.StringField())
    role = me.StringField(required=True)
    is_image = me.BooleanField(required=False, default=False)

    user = me.ReferenceField(UserModel, reverse_delete_rule=me.CASCADE)
    room = me.ReferenceField(ChatRoomModel, reverse_delete_rule=me.CASCADE)

    meta = {"collection": "chat_history"}
