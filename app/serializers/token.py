from ..models import AccountActiveModel, ResetPasswordModel
from ..dataclasses import AccessTokenSchema
from .interfaces import SerializerInterface
from typing import Union


class TokenSerializer(SerializerInterface):
    def serialize(
        self,
        token_data: Union[AccountActiveModel, ResetPasswordModel, AccessTokenSchema],
        id_is_null: bool = False,
        access_token_is_null: bool = False,
        token_is_null: bool = False,
        otp_is_null: bool = False,
        created_at_is_null: bool = False,
        updated_at_is_null: bool = False,
        expired_at_is_null: bool = False,
    ) -> dict:
        data = {}
        if not created_at_is_null:
            data["created_at"] = token_data.created_at
        if isinstance(token_data, (AccountActiveModel, ResetPasswordModel)):
            if not id_is_null:
                data["id"] = str(token_data.id) if token_data.id else None
            if not token_is_null:
                data["token"] = token_data.token
            if not created_at_is_null:
                data["created_at"] = token_data.created_at.isoformat()
            if not updated_at_is_null:
                data["updated_at"] = token_data.updated_at.isoformat()
            if not expired_at_is_null:
                data["expired_at"] = token_data.expired_at.isoformat()
            if not otp_is_null:
                data["otp"] = token_data.otp
        if isinstance(token_data, AccessTokenSchema):
            if not access_token_is_null:
                data["access_token"] = token_data.access_token
        return data
