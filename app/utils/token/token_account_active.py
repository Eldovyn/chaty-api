from .token import Token
from itsdangerous.url_safe import URLSafeSerializer
from ...config import salt_account_active, secret_key_account_active


class TokenAccountActive(Token):
    @staticmethod
    async def insert(user_id, created_at):
        s = URLSafeSerializer(
            salt_account_active, salt=secret_key_account_active
        )
        token = s.dumps({"user_id": user_id, "created_at": created_at.isoformat()})
        return token

    @staticmethod
    async def get(token):
        s = URLSafeSerializer(
            salt_account_active, salt=secret_key_account_active
        )
        try:
            s.loads(token)["user_id"]
            s.loads(token)["created_at"]
        except:
            return None
        else:
            return s.loads(token)
