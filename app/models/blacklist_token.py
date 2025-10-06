import mongoengine as me


class BlacklistTokenModel(me.Document):
    created_at = me.IntField(required=True)

    user = me.ReferenceField("UserModel", reverse_delete_rule=me.CASCADE)

    meta = {"collection": "blacklist_token"}
