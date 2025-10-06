from .database import Database
from ..models import AccountActiveModel, UserModel
from datetime import timezone


class AccountActiveDatabase(Database):
    @staticmethod
    async def insert(email, token, otp, expired_at):
        data_user = UserModel.objects(email=email.lower()).first()
        if not data_user:
            return None

        data_account_active = AccountActiveModel.objects(user=data_user).first()
        if not data_account_active:
            data_account_active = AccountActiveModel(
                user=data_user,
                token=token,
                expired_at=expired_at,
                otp=otp,
            )
        else:
            data_account_active.otp = otp
            data_account_active.token = token
            data_account_active.expired_at = expired_at
        data_account_active.save()

        return data_account_active

    @staticmethod
    async def get(category, **kwargs):
        token = kwargs.get("token")
        created_at = kwargs.get("created_at")
        if category == "by_token":
            if data_account_active := AccountActiveModel.objects(
                token=token
            ).first():
                if (
                    data_account_active.expired_at.replace(tzinfo=timezone.utc)
                    > created_at
                ):
                    return data_account_active
                else:
                    data_account_active.user.save()
                    data_account_active.delete()

    @staticmethod
    async def delete(category, **kwargs):
        pass

    @staticmethod
    async def update(category, **kwargs):
        user_id = kwargs.get("user_id")
        token = kwargs.get("token")
        otp = kwargs.get("otp")
        if category == "user_active_by_token":
            if user_data := UserModel.objects(id=user_id).first():
                if data_account_active := AccountActiveModel.objects(
                    user=user_data, token=token, otp=otp
                ).first():
                    user_data.is_active = True
                    user_data.save()
                    data_account_active.delete()
                    return data_account_active
