from flask import request
from flask_limiter.util import get_remote_address


def limiter_key():
    if request.method == "OPTIONS":
        return None
    return get_remote_address()
