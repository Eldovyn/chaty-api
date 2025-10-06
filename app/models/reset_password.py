import mongoengine as me
from .base import BaseDocument


class ResetPasswordModel(BaseDocument):
    token = me.StringField(required=True)
    expired_at = me.DateTimeField(required=True)

    user = me.ReferenceField("UserModel", reverse_delete_rule=me.CASCADE)

    meta = {"collection": "reset_password"}
