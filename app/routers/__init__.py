from .auth import auth_router
from .users import users_router


def register_blueprints(app):
    app.register_blueprint(auth_router, url_prefix="/auth")
    app.register_blueprint(users_router, url_prefix="/users")
