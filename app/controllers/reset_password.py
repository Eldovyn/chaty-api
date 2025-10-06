from ..databases import UserDatabase, ResetPasswordDatabase
from flask import jsonify, request, make_response
from ..utils import (
    TokenAccountActive,
    SendEmail,
    Validation,
    generate_etag,
)
import datetime
from ..config import web_short_me
from ..serializers import UserSerializer, TokenSerializer


class ResetPasswordController:
    def __init__(self):
        self.user_seliazer = UserSerializer()
        self.token_serializer = TokenSerializer()

    async def get_user_reset_password_verification(self, token, timestamp):
        errors = {}
        await Validation.validate_token(errors, token, "email_token_reset_password")
        if errors:
            return jsonify({"errors": errors, "message": "validations error"}), 400
        if not (
            user_token := await ResetPasswordDatabase.get(
                "by_token_email", token=token, created_at=timestamp
            )
        ):
            return (
                jsonify(
                    {
                        "message": "validation errors",
                        "errors": {"token": ["IS_INVALID"]},
                    }
                ),
                422,
            )
        current_user = self.user_seliazer.serialize(user_token.user)
        token_data = self.token_serializer.serialize(user_token)
        combined_data = {**current_user, **token_data}
        etag = generate_etag(combined_data)

        client_etag = request.headers.get("If-None-Match")
        if client_etag == etag:
            return make_response("", 304)

        response_data = {
            "message": "successfully get account active information",
            "data": token_data,
            "user": current_user,
        }

        response = make_response(jsonify(response_data), 200)
        response.headers["Content-Type"] = "application/json"
        response.headers["ETag"] = etag
        return response

    async def user_reset_password_verification(
        self, token, new_password, confirm_password, timestamp
    ):
        from ..extensions import bcrypt

        errors = {}
        await Validation.validate_token(errors, token, "email_token_reset_password")
        await Validation.validate_password(errors, new_password, confirm_password)
        if errors:
            return jsonify({"errors": errors, "message": "validations error"}), 400
        if not (
            user_token := await ResetPasswordDatabase.get(
                "by_token_email", token=token, created_at=timestamp
            )
        ):
            return (
                jsonify(
                    {
                        "message": "validation errors",
                        "errors": {"token": ["IS_INVALID"]},
                    }
                ),
                422,
            )
        result_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        await ResetPasswordDatabase.delete(
            "user_password_by_token_email",
            token=token,
            user_id=f"{user_token.user.id}",
            new_password=result_password,
            created_at=timestamp,
        )
        current_user = self.user_seliazer.serialize(user_token.user)
        token_data = self.token_serializer.serialize(user_token)
        return (
            jsonify(
                {
                    "message": "successfully change password",
                    "data": token_data,
                    "user": current_user,
                }
            ),
            201,
        )

    async def send_reset_password_email(self, email, timestamp):
        errors = {}
        await Validation.validate_required_text(errors, "email", email)
        if errors:
            return jsonify({"errors": errors, "message": "validations error"}), 400
        if not (user_data := await UserDatabase.get("by_email", email=email)):
            return (
                jsonify({"message": "user not found"}),
                404,
            )
        if user_data.provider != "auth_internal":
            return (
                jsonify(
                    {
                        "message": "validation errors",
                        "errors": {"email": ["IS_INVALID"]},
                    }
                ),
                422,
            )
        expired_at = timestamp + datetime.timedelta(minutes=5)
        token = await TokenAccountActive.insert(
            f"{user_data.id}"
        )
        reset_password_data = await ResetPasswordDatabase.insert(
            email, token, expired_at
        )
        SendEmail.send_email(
            "Reset Password",
            [user_data.email],
            f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password</title>
</head>
<body>
    <p>Hello {user_data.username},</p>
    <p>Someone has requested a link to reser password, and you can do this through the link below.</p>
    <p>
        <a href="{web_short_me}/reset-password/user?token={token}">
            Click here to activate your account
        </a>
    </p>
    <p>If you didn't request this, please ignore this email.</p>
</body>
</html>
                """,
        )
        current_user = self.user_seliazer.serialize(reset_password_data.user)
        token_data = self.token_serializer.serialize(
            reset_password_data, token_email_is_null=True
        )
        return (
            jsonify(
                {
                    "message": "successfully send reset password email",
                    "data": token_data,
                    "user": current_user,
                }
            ),
            201,
        )
