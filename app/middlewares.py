import datetime
from flask import request, make_response


def register_middlewares(app):
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, If-None-Match"
        )
        response.headers["Access-Control-Expose-Headers"] = "ETag"
        return response

    @app.before_request
    def before_request():
        request.timestamp = datetime.datetime.now(datetime.timezone.utc)
        if request.method == "OPTIONS":
            response = make_response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization,If-None-Match"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET,PUT,POST,DELETE,OPTIONS"
            )
            return response, 200
