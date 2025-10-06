from flask import request
from flask_socketio import SocketIO, emit
from ..utils import Validation
import asyncio


def register_validate_register_socketio_events(socket_io: SocketIO):
    validation = Validation()

    @socket_io.on("connect", namespace="/validate-register")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/validate-register")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/validate-register")
    def handle_validation(data):
        errors = {}
        username = data.get("username", "")
        email = data.get("email", "")
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        provider = data.get("provider", "")
        asyncio.run(validation.validate_username(errors, username))
        asyncio.run(validation.validate_email(errors, email))
        asyncio.run(validation.validate_password(errors, password, confirm_password))
        asyncio.run(validation.validate_provider(errors, provider))
        emit(
            "validation",
            {"errors": errors, "success": len(errors) == 0},
            namespace="/validate-register",
        )
