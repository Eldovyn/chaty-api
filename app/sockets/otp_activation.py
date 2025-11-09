from flask import request
from flask_socketio import SocketIO
from ..utils import Validation
from ..databases import AccountActiveDatabase
import datetime


def register_otp_activation_socketio_events(socket_io: SocketIO):
    validation = Validation()

    def _do_validation(sid, data):
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        errors = {}
        if "token" in data:
            validation.validate_token_sync(errors, "token", data["token"])
        else:
            errors.setdefault("token", []).append("IS_REQUIRED")
        if "otp" in data:
            validation.validate_otp_sync(errors, data["otp"])
        else:
            errors.setdefault("otp", []).append("IS_REQUIRED")
        if errors:
            socket_io.emit(
                "validation",
                {
                    "errors": errors,
                    "success": len(errors) == 0,
                    "message": "validation errors",
                },
                namespace="/otp-activation",
                to=sid,
            )
            return
        if not (
            user_token := AccountActiveDatabase.get_sync(
                "by_token", token=data["token"], created_at=timestamp
            )
        ):
            if "token" not in errors:
                errors["token"] = ["IS_INVALID"]
        try:
            if user_token.otp != data["otp"]:
                errors.setdefault("otp", []).append("IS_INVALID")
        except:
            if "token" not in errors:
                errors["token"] = ["IS_INVALID"]
        if errors:
            socket_io.emit(
                "validation",
                {
                    "errors": errors,
                    "success": len(errors) == 0,
                    "message": "validation errors",
                },
                namespace="/otp-activation",
            )
            return
        AccountActiveDatabase.update_sync(
            "user_active_by_token",
            token=user_token.token,
            user_id=f"{user_token.user.id}",
            otp=user_token.otp,
        )
        socket_io.emit(
            "validation",
            {
                "errors": errors,
                "success": len(errors) == 0,
                "message": "email verified successfully",
            },
            namespace="/otp-activation",
        )

    @socket_io.on("connect", namespace="/otp-activation")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/otp-activation")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/otp-activation")
    def handle_validation(data):
        sid = request.sid
        socket_io.start_background_task(_do_validation, sid, data)
