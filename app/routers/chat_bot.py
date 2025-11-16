from flask import Blueprint, request
from ..utils import jwt_required
from ..controllers import ChatBotController

chat_bot_router = Blueprint("chat_bot_router", __name__)
chat_bot_controller = ChatBotController()


@chat_bot_router.post("/messages")
@jwt_required()
async def user_login():
    user = request.user
    form = request.form
    files = request.files
    text = form.get("text", "")
    room = form.get("room", "")
    docs = files.get("file", None)
    return await chat_bot_controller.create_message(user, text, room, docs)


@chat_bot_router.get("/messages")
@jwt_required()
async def get_messages():
    user = request.user
    return await chat_bot_controller.get_messages(user)


@chat_bot_router.get("/rooms")
@jwt_required()
async def get_all_rooms():
    user = request.user
    return await chat_bot_controller.get_all_rooms(user)
