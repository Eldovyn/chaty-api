import mongoengine as me
from .base import BaseDocument


class BlacklistTokenModel(BaseDocument):
    created_at = me.IntField(required=True)

    user = me.ReferenceField("UserModel", reverse_delete_rule=me.CASCADE)

    meta = {"collection": "blacklist_token"}
