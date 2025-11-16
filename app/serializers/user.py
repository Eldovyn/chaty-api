from ..models import UserModel
from .interfaces import SerializerInterface


class UserSerializer(SerializerInterface):
    def serialize(
        self,
        user: UserModel,
        id_is_null: bool = False,
        email_is_null: bool = False,
        avatar_is_null: bool = False,
        username_is_null: bool = False,
        created_at_is_null: bool = False,
        updated_at_is_null: bool = False,
        is_active_is_null: bool = False,
        provider_is_null: bool = False,
        role_is_null: bool = False,
    ) -> dict:
        data = {}
        if not id_is_null:
            data["id"] = str(user.id) if user.id else None
        if not email_is_null:
            data["email"] = user.email
        if not username_is_null:
            data["username"] = user.username
        if not avatar_is_null:
            data["avatar"] = user.avatar
        if not created_at_is_null:
            data["created_at"] = user.created_at.isoformat()
        if not updated_at_is_null:
            data["updated_at"] = user.updated_at.isoformat()
        if not is_active_is_null:
            data["is_active"] = user.is_active
        if not provider_is_null:
            data["provider"] = user.provider
        if not role_is_null:
            data["role"] = user.role
        return data
