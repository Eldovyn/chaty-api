from .auth import auth_router
from .users import users_router
from .chat_bot import chat_bot_router


def register_blueprints(app):
    app.register_blueprint(auth_router, url_prefix="/auth")
    app.register_blueprint(users_router, url_prefix="/users")
    app.register_blueprint(chat_bot_router, url_prefix="/chat-bot")
