import mongoengine as me
from .base import BaseDocument


class UserModel(BaseDocument):
    username = me.StringField(required=True, min_length=3, max_length=30)
    email = me.StringField(required=True, unique=True, min_length=6, max_length=254)
    password = me.StringField(required=False)
    provider = me.StringField(required=True)
    avatar = me.StringField(required=True)
    role = me.StringField(required=False, default="user")
    is_active = me.BooleanField(required=False, default=False)
    updated_email_at = me.DateTimeField(required=False)

    meta = {"collection": "users"}

    async def unique_field(self):
        if self.username:
            self.username = self.username.lower()
        if self.email:
            self.email = self.email.lower()
