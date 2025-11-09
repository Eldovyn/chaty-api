from .account_activation import *
from .reset_password_changed import *
from .validate_register import *
from .validate_login import *
from .otp_activation import *
from .chat_bot import *


def register_socket_io(socket_io):
    register_account_activation_socketio_events(socket_io)
    register_reset_password_changed_socketio_events(socket_io)
    register_validate_register_socketio_events(socket_io)
    register_validate_login_socketio_events(socket_io)
    register_otp_activation_socketio_events(socket_io)
    register_chat_bot_socketio_events(socket_io)
