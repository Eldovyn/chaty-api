from flask import Flask, render_template
from .celery_app import celery_init_app


def create_app(test_config=None):
    import os
    from .config import Config

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    global celery_app
    celery_app = celery_init_app(app)

    from .tasks import register_tasks

    register_tasks(celery_app)

    from .extensions import db, mail, bcrypt, limiter, init_cloudinary, socket_io

    bcrypt.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    # limiter.init_app(app)
    socket_io.init_app(app)
    init_cloudinary()

    from .utils import load_key_pair

    global private_key, public_key
    private_key, public_key = load_key_pair(BASE_DIR)

    from .routers import register_blueprints
    from .error_handlers import register_error_handlers
    from .middlewares import register_middlewares
    from .sockets import register_socket_io

    @app.route("/")
    def index():
        return render_template("index.html")

    register_socket_io(socket_io)
    register_blueprints(app)
    register_error_handlers(app)
    register_middlewares(app)

    return app
