from flask import request
from flask_socketio import SocketIO
from ..utils import Validation


def register_validate_register_socketio_events(socket_io: SocketIO):
    validation = Validation()

    def _do_validation(data):
        errors = {}
        username = data.get("username", "")
        email = data.get("email", "")
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        provider = data.get("provider", "")
        validation.validate_username_sync(errors, username)
        validation.validate_email_sync(errors, email)
        validation.validate_provider_sync(errors, provider)
        validation.validate_password_sync(errors, password, confirm_password)
        socket_io.emit(
            "validation",
            {"errors": errors, "success": len(errors) == 0},
            namespace="/validate-register",
        )

    @socket_io.on("connect", namespace="/validate-register")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/validate-register")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/validate-register")
    def handle_validation(data):
        socket_io.start_background_task(_do_validation, data)
