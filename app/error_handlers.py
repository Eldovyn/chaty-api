from flask import jsonify
from werkzeug.exceptions import (
    BadRequest,
    NotFound,
    InternalServerError,
    TooManyRequests,
    MethodNotAllowed,
)


def register_error_handlers(app):
    @app.errorhandler(BadRequest)
    async def handle_bad_request(e):
        return jsonify({"message": str(e.description)}), 400

    @app.errorhandler(NotFound)
    async def handle_not_found(e):
        return jsonify({"message": "resource not found"}), 404

    @app.errorhandler(TooManyRequests)
    async def handle_too_many_requests(e):
        return jsonify({"message": "too many requests"}), 429

    @app.errorhandler(MethodNotAllowed)
    async def handle_internal_server_error(e):
        return jsonify({"message": "method not allowed"}), 405
