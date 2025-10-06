import mongoengine as me


class OtpEmailModel(me.Document):
    otp = me.StringField(required=True)
    created_at = me.IntField(required=True)
    updated_at = me.IntField(required=True)
    expired_at = me.IntField(required=True)

    user = me.ReferenceField("UserModel", reverse_delete_rule=me.CASCADE)

    meta = {"collection": "otp_email"}
