from flask import Blueprint, request
from ..utils import jwt_required
from ..controllers import ProfileController

users_router = Blueprint("users_router", __name__)
profile_controller = ProfileController()


@users_router.get("/@me")
@jwt_required()
async def user_me():
    user = request.user
    return await profile_controller.user_me(user)


@users_router.get("/default-avatar")
async def default_avatar():
    return await profile_controller.default_avatar()


@users_router.patch("/user")
@jwt_required()
async def update_profile():
    user = request.user
    timestamp = request.timestamp
    forms = request.form
    files = request.files
    first_name = forms.get("first_name", None)
    last_name = forms.get("last_name", None)
    country = forms.get("country", None)
    position = forms.get("position", None)
    email = forms.get("email", None)
    phone_number = forms.get("phone_number", None)
    avatar = files.get("avatar", None)
    return await profile_controller.update_profile(
        user,
        first_name,
        last_name,
        country,
        position,
        email,
        phone_number,
        avatar,
        timestamp,
    )


@users_router.delete("/user")
@jwt_required()
async def delete_user():
    user = request.user
    timestamp = request.timestamp
    return await profile_controller.delete_user(user, timestamp)
