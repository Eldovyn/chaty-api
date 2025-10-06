import jwt


class AuthJwt:
    @staticmethod
    async def generate_jwt_async(user_id, datetime):
        from .. import private_key

        payload = {"sub": user_id, "iat": datetime}
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return token

    @staticmethod
    def generate_jwt_sync(user_id, datetime):
        from .. import private_key

        payload = {"sub": user_id, "iat": datetime}
        token = jwt.encode(payload, private_key, algorithm="RS256")
        return token

    @staticmethod
    async def verify_token_async(token):
        from .. import public_key

        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def verify_token_sync(token):
        from .. import public_key

        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
