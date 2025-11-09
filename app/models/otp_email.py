import mongoengine as me
from .base import BaseDocument
from .user import UserModel


class OtpEmailModel(BaseDocument):
    otp = me.StringField(required=True)
    expired_at = me.IntField(required=True)

    user = me.ReferenceField(UserModel, reverse_delete_rule=me.CASCADE)

    meta = {"collection": "otp_email"}
