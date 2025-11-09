from flask import request
from flask_socketio import SocketIO
from ..utils import Validation


def register_validate_login_socketio_events(socket_io: SocketIO):
    validation = Validation()

    def _do_validation(data):
        errors = {}
        email = data.get("email", "")
        password = data.get("password", "")
        provider = data.get("provider", "")
        validation.validate_required_text_sync(errors, "email", email)
        validation.validate_required_text_sync(errors, "password", password)
        validation.validate_provider_sync(errors, provider)
        socket_io.emit(
            "validation",
            {"errors": errors, "success": len(errors) == 0},
            namespace="/validate-login",
        )

    @socket_io.on("connect", namespace="/validate-login")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/validate-login")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/validate-login")
    def handle_validation(data):
        socket_io.start_background_task(_do_validation, data)
