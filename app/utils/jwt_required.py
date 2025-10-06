import inspect
from functools import wraps
from flask import request, jsonify
from ..utils import AuthJwt
from ..models import UserModel, BlacklistTokenModel


def jwt_required():
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = _check_jwt()
            if isinstance(result, tuple):
                return result
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = _check_jwt()
            if isinstance(result, tuple):
                return result
            return func(*args, **kwargs)

        def _check_jwt():
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.lower().startswith("bearer "):
                return (
                    jsonify(
                        {
                            "message": "invalid authorization header",
                        }
                    ),
                    401,
                )

            token = auth_header.split()[1]
            payload = AuthJwt.verify_token_sync(token)

            if payload is None:
                return (
                    jsonify(
                        {
                            "message": "invalid or expired token",
                        }
                    ),
                    401,
                )

            user_id = payload.get("sub")
            iat = payload.get("iat")

            if not user_id:
                return (
                    jsonify(
                        {
                            "message": "invalid or expired token",
                        }
                    ),
                    401,
                )

            user_data = UserModel.objects(id=user_id).first()
            if not user_data:
                return (
                    jsonify(
                        {
                            "message": "invalid or expired token",
                        }
                    ),
                    401,
                )

            if not iat > user_data.updated_at and not iat == user_data.updated_at:
                return (
                    jsonify(
                        {
                            "message": "invalid or expired token",
                        }
                    ),
                    401,
                )

            if BlacklistTokenModel.objects(created_at=iat).first():
                return (
                    jsonify(
                        {
                            "message": "invalid or expired token",
                        }
                    ),
                    401,
                )

            if not user_data.is_active:
                return (
                    jsonify(
                        {
                            "message": "user is not active",
                        }
                    ),
                    401,
                )

            request.user = user_data
            request.token = payload
            return None

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
