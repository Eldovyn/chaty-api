from ..databases import UserDatabase
from flask import jsonify, send_from_directory, request, make_response
from ..utils import SendEmail
from email_validator import validate_email
from ..serializers import UserSerializer
from werkzeug.utils import secure_filename
import os
import cloudinary.uploader
from ..utils import generate_etag


class ProfileController:
    def __init__(self):
        self.user_seliazer = UserSerializer()

    async def default_avatar(self):
        return send_from_directory(
            "static/images", "default-avatar.webp", mimetype="image/png"
        )

    async def update_profile(
        self,
        user,
        first_name,
        last_name,
        country,
        position,
        email,
        phone_number,
        avatar,
        timestamp,
    ):
        errors = {}
        if first_name:
            if not isinstance(first_name, str):
                errors.setdefault("first_name", []).append("MUST_TEXT")
            if isinstance(first_name, str) and len(first_name) < 5:
                errors.setdefault("first_name", []).append("TOO_SHORT")
            if isinstance(first_name, str) and len(first_name) > 15:
                errors.setdefault("first_name", []).append("TOO_LONG")
        if last_name:
            if not isinstance(last_name, str):
                errors.setdefault("last_name", []).append("MUST_TEXT")
            if isinstance(last_name, str) and len(last_name) < 5:
                errors.setdefault("last_name", []).append("TOO_SHORT")
            if isinstance(last_name, str) and len(last_name) > 15:
                errors.setdefault("last_name", []).append("TOO_LONG")
        if position:
            if not isinstance(position, str):
                errors.setdefault("position", []).append("MUST_TEXT")
            if isinstance(position, str) and len(position) < 5:
                errors.setdefault("position", []).append("TOO_SHORT")
            if isinstance(position, str) and len(position) > 50:
                errors.setdefault("position", []).append("TOO_LONG")
        if phone_number:
            if not isinstance(phone_number, str):
                errors.setdefault("phone_number", []).append("MUST_TEXT")
        if email:
            if not isinstance(email, str):
                errors.setdefault("email", []).append("MUST_TEXT")
            if isinstance(email, str) and len(email) < 5:
                errors.setdefault("email", []).append("TOO_SHORT")
            if isinstance(email, str) and len(email) > 50:
                errors.setdefault("email", []).append("TOO_LONG")
            try:
                valid = validate_email(email)
                email = valid.email
            except:
                errors.setdefault("email", []).append("IS_INVALID")
        if avatar:
            filename = secure_filename(avatar.filename)
            ext = os.path.splitext(filename)[1].lower().replace(".", "")
            if ext not in ("jpg", "jpeg", "png", "webp"):
                errors.setdefault("proof", []).append("IS_INVALID")
        if errors:
            return jsonify({"errors": errors, "message": "validation errors"}), 400
        if avatar:
            result_cloudinary = cloudinary.uploader.upload(avatar)
            avatar = result_cloudinary["secure_url"]
        user_update = await UserDatabase.update(
            "profile",
            user_id=f"{user.id}",
            last_name=last_name,
            first_name=first_name,
            country=country,
            position=position,
            email=email,
            phone_number=phone_number,
            avatar=avatar,
        )
        SendEmail.send_email(
            "Update Profile",
            [user_update.email],
            f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Update Profile</title>
</head>
<body>
    <p>Hello {user_update.first_name} {user_update.last_name},</p>
    <p>your profile has been updated</p>
</body>
</html>
                """,
        )
        user_seliazer = self.user_seliazer.serialize(user_update)
        return (
            jsonify(
                {
                    "message": "successfully update profile",
                    "data": user_seliazer,
                }
            ),
            201,
        )

    async def current_user(self, user):
        print("user:", user.username)
        current_user = self.user_seliazer.serialize(user)
        print("current_user:", current_user)

        etag = generate_etag(current_user)

        client_etag = request.headers.get("If-None-Match")
        if client_etag == etag:
            return make_response("", 304)

        response_data = {
            "data": current_user,
            "message": "successfully get user",
        }

        response = make_response(jsonify(response_data), 200)
        response.headers["Content-Type"] = "application/json"
        response.headers["ETag"] = etag
        return response
