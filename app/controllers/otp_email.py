from ..databases import OtpEmailDatabase
from ..utils import SendEmail
from flask import jsonify
import string
import datetime
import random
from ..serializers import UserSerializer


class OtpEmailController:
    def __init__(self):
        self.user_seliazer = UserSerializer()

    async def otp_email(self, user, timestamp):
        karakter = string.ascii_uppercase + string.digits
        expired_at = timestamp + datetime.timedelta(minutes=5)
        otp = "".join(random.choices(karakter, k=4))
        if not (
            data_otp := await OtpEmailDatabase.insert(
                user.id, otp, int(timestamp.timestamp()), int(expired_at.timestamp())
            )
        ):
            return (
                jsonify(
                    {
                        "message": "invalid or expired token",
                    }
                ),
                401,
            )
        SendEmail.send_email_otp(user, otp)
        return (
            jsonify(
                {
                    "message": "successfully send otp",
                    "data": {
                        "id": f"{data_otp.id}",
                        "created_at": data_otp.created_at,
                        "expired_at": data_otp.expired_at,
                    },
                }
            ),
            201,
        )
