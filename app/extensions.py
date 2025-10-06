from flask_mongoengine import MongoEngine
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from .config import (
    celery_url,
    cloudinary_api_secret,
    cloudinary_api_key,
    cloudinary_cloud_name,
)
from .utils import limiter_key
import cloudinary
from flask_socketio import SocketIO

db = MongoEngine()
mail = Mail()
bcrypt = Bcrypt()

limiter = Limiter(
    key_func=limiter_key,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=f"{celery_url}",
)

socket_io = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    message_queue=f"{celery_url}",
    max_http_buffer_size=100 * 1024 * 1024,
)


def init_cloudinary():
    cloudinary.config(
        secure=True,
        api_secret=cloudinary_api_secret,
        api_key=cloudinary_api_key,
        cloud_name=cloudinary_cloud_name,
    )
