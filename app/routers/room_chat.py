from flask import Blueprint, request
from ..utils import jwt_required
from ..controllers import ChatRoomController

chat_room = Blueprint("chat_room", __name__)
chat_room_controller = ChatRoomController()


@chat_room.get("/")
@jwt_required()
async def get_all_rooms():
    user = request.user
    return await chat_room_controller.get_all_rooms(user)


@chat_room.delete("/")
@jwt_required()
async def clear_rooms():
    user = request.user
    return await chat_room_controller.clear_rooms(user)
