from ..databases import UserDatabase, AccountActiveDatabase
from flask import jsonify, url_for
import requests
from ..utils import (
    TokenAccountActive,
    SendEmail,
    AuthJwt,
    Validation,
    generate_otp,
)
import datetime
from ..config import web_short_me
from ..serializers import UserSerializer, TokenSerializer
from ..dataclasses import AccessTokenSchema


class RegisterController:
    def __init__(self):
        self.user_seliazer = UserSerializer()
        self.token_serializer = TokenSerializer()

    async def user_register(
        self,
        provider,
        token,
        username,
        email,
        password,
        confirm_password,
        timestamp,
    ):
        from ..extensions import bcrypt

        access_token = None
        token_web = None

        try:
            errors = {}
            await Validation.validate_provider(errors, provider)
            if provider == "google":
                await Validation.validate_required_text(errors, "token", token)
                if errors:
                    return (
                        jsonify(
                            {
                                "errors": errors,
                                "message": "validations error",
                            }
                        ),
                        400,
                    )
                url = f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={token}"
                response = requests.get(url)
                resp = response.json()
                try:
                    username = resp["name"]
                    email = resp["email"]
                    avatar = resp["picture"]
                except KeyError:
                    return (
                        jsonify(
                            {
                                "message": "validations error",
                            }
                        ),
                        400,
                    )
                if user_data := await UserDatabase.get("by_email", email=email):
                    return (
                        jsonify(
                            {
                                "message": "the user already exists",
                            }
                        ),
                        409,
                    )
                user_data = await UserDatabase.insert(
                    provider, avatar, username, email, None
                )
                user_me = self.user_seliazer.serialize(user_data)
                access_token = await AuthJwt.generate_jwt_async(
                    f"{user_data.id}", timestamp
                )
                access_token_model = AccessTokenSchema(
                    access_token=access_token, created_at=timestamp
                )
                token_data = self.token_serializer.serialize(access_token_model)
            else:
                await Validation.validate_username(errors, username)
                await Validation.validate_email(errors, email)
                await Validation.validate_password(errors, password, confirm_password)
                if errors:
                    return (
                        jsonify(
                            {
                                "errors": errors,
                                "message": "validations error",
                            }
                        ),
                        400,
                    )
                result_password = bcrypt.generate_password_hash(password).decode(
                    "utf-8"
                )
                avatar = url_for(
                    "static", filename="images/default-avatar.webp", _external=True
                )
                if user_data := await UserDatabase.get("by_email", email=email):
                    return (
                        jsonify(
                            {
                                "message": "the user already exists",
                            }
                        ),
                        409,
                    )
            if provider != "google":
                user_data = await UserDatabase.insert(
                    provider,
                    f"{avatar}",
                    username,
                    email,
                    result_password,
                )
                user_me = self.user_seliazer.serialize(user_data)
                expired_at = timestamp + datetime.timedelta(minutes=5)
                token = await TokenAccountActive.insert(
                    f"{user_data.id}", timestamp
                )
                otp = generate_otp(4)
                token_account_active = await AccountActiveDatabase.insert(
                    email, token, otp, expired_at
                )
                SendEmail.send_email(
                    "Verification Your Account",
                    [user_data.email],
                    f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Active</title>
</head>
<body>
    <p>Hello {user_data.username},</p>
    <p>Someone has requested a link to verify your account, and you can do this through the link below.</p>
    <p>your otp is {otp}.</p>
    <p>
        <a href="{web_short_me}/account-active?token={token}">
            Click here to activate your account
        </a>
    </p>
    <p>If you didn't request this, please ignore this email.</p>
</body>
</html>
                """,
                )
                token_data = self.token_serializer.serialize(
                    token_account_active, token_is_null=True
                )
            return (
                jsonify(
                    {
                        "message": "user registered successfully",
                        "data": user_me,
                        "token": token_data,
                    }
                ),
                201,
            )
        except Exception as e:
            return jsonify({"message": f"{e}"}), 400
