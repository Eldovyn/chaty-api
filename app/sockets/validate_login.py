from flask import request
from flask_socketio import SocketIO, emit
from ..utils import Validation
import asyncio


def register_validate_login_socketio_events(socket_io: SocketIO):
    validation = Validation()

    @socket_io.on("connect", namespace="/validate-login")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/validate-login")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/validate-login")
    def handle_validation(data):
        errors = {}
        email = data.get("email", "")
        password = data.get("password", "")
        provider = data.get("provider", "")
        asyncio.run(validation.validate_required_text(errors, 'email', email))
        asyncio.run(validation.validate_required_text(errors, 'password', password))
        asyncio.run(validation.validate_provider(errors, provider))
        emit(
            "validation",
            {"errors": errors, "success": len(errors) == 0},
            namespace="/validate-login",
        )
