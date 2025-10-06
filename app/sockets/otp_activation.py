from flask import request
from flask_socketio import SocketIO, emit
from ..utils import Validation
import asyncio
from ..databases import AccountActiveDatabase
import datetime


def register_otp_activation_socketio_events(socket_io: SocketIO):
    validation = Validation()

    @socket_io.on("connect", namespace="/otp-activation")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/otp-activation")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("validation", namespace="/otp-activation")
    def handle_validation(data):
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        errors = {}
        token = data.get("token", "")
        otp = data.get("otp", "")
        errors = {}
        asyncio.run(validation.validate_token(errors, token, "token_account_active"))
        asyncio.run(validation.validate_otp(errors, otp))
        if errors:
            emit(
                "validation",
                {"errors": errors, "success": len(errors) == 0, 'message': 'validation errors'},
                namespace="/otp-activation",
            )
            return
        if not (
            user_token := asyncio.run(
                AccountActiveDatabase.get("by_token", token=token, created_at=timestamp)
            )
        ):
            if "token" not in errors:
                errors["token"] = ["IS_INVALID"]
        try:
            if user_token.otp != otp:
                errors.setdefault("otp", []).append("IS_INVALID")
        except:
            if "token" not in errors:
                errors["token"] = ["IS_INVALID"]
        if errors:
            emit(
                "validation",
                {"errors": errors, "success": len(errors) == 0, 'message': 'validation errors'},
                namespace="/otp-activation",
            )
            return
        asyncio.run(
            AccountActiveDatabase.update(
                "user_active_by_token",
                token=user_token.token,
                user_id=f"{user_token.user.id}",
                otp=user_token.otp,
            )
        )
        emit(
            "validation",
            {"errors": errors, "success": len(errors) == 0, 'message': 'email verified successfully'},
            namespace="/otp-activation",
        )
