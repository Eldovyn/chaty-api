from flask import request
from flask_socketio import SocketIO, disconnect, join_room, emit
from ..models import AccountActiveModel
import time
import datetime
from datetime import timezone


def register_account_activation_socketio_events(socket_io: SocketIO):
    countdowns = {}

    def countdown_thread(room, token):
        while True:
            now = time.time()
            expired_time = countdowns.get(room)
            if not expired_time:
                break
            remaining = int(expired_time - now)
            if remaining <= 0:
                socket_io.emit(
                    "countdown",
                    {"remaining": 0},
                    room=room,
                    namespace="/account-activation",
                )
                if data_token := AccountActiveModel.objects(token=token).first():
                    data_token.delete()
                socket_io.emit(
                    "expired",
                    {"status": "expire", 'message': 'your session expired'},
                    room=room,
                    namespace="/account-activation",
                )
                del countdowns[room]
                if hasattr(countdown_thread, "running_rooms"):
                    countdown_thread.running_rooms.discard(room)
                break
            else:
                socket_io.emit(
                    "countdown",
                    {"remaining": remaining},
                    room=room,
                    namespace="/account-activation",
                )
            socket_io.sleep(1)

    @socket_io.on("connect", namespace="/account-activation")
    def handle_connect():
        print(f"User connected from IP: {request.remote_addr}")

    @socket_io.on("disconnect", namespace="/account-activation")
    def handle_disconnect():
        print(f"User disconnected from IP: {request.remote_addr}")

    @socket_io.on("join", namespace="/account-activation")
    def handle_join(data):
        token = data.get("token")
        if not token:
            disconnect()
            return

        user_token = AccountActiveModel.objects(token=token).first()
        if not user_token:
            disconnect()
            return

        room = f"account-activation-{user_token.id}"
        join_room(room)

        now = time.time()

        expired_dt = user_token.expired_at

        if isinstance(expired_dt, datetime.datetime):
            if expired_dt.tzinfo is None:
                expired_dt = expired_dt.replace(tzinfo=timezone.utc)
            expired_time = expired_dt.timestamp()
        else:
            expired_time = now + 5 * 60

        countdowns[room] = expired_time

        remaining = max(0, int(expired_time - now))
        emit("countdown", {"remaining": remaining})

        if not hasattr(countdown_thread, "running_rooms"):
            countdown_thread.running_rooms = set()

        if room not in countdown_thread.running_rooms:
            countdown_thread.running_rooms.add(room)
            socket_io.start_background_task(countdown_thread, room, token)
