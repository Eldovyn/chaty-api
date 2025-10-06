import mongoengine as me
from .base import BaseDocument


class AccountActiveModel(BaseDocument):
    token = me.StringField(required=True)
    otp = me.StringField(required=True)
    expired_at = me.DateTimeField(required=True)

    user = me.ReferenceField("UserModel", reverse_delete_rule=me.CASCADE)

    meta = {"collection": "account_active"}
