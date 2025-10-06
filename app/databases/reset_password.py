from .database import Database
from ..models import ResetPasswordModel, UserModel
from datetime import timezone


class ResetPasswordDatabase(Database):
    @staticmethod
    async def insert(email, token_web, token_email, expired_at):
        if data_user := UserModel.objects(email=email.lower()).first():
            if data_account_active := ResetPasswordModel.objects(
                user=data_user
            ).first():
                data_account_active.token_web = token_web
                data_account_active.token_email = token_email
                data_account_active.expired_at = expired_at
                data_account_active.save()
                return data_account_active
            account_active_data = ResetPasswordModel(
                user=data_user,
                token_web=token_web,
                token_email=token_email,
                expired_at=expired_at,
            )
            account_active_data.save()
            return account_active_data

    @staticmethod
    async def get(category, **kwargs):
        token = kwargs.get("token")
        created_at = kwargs.get("created_at")
        if category == "by_token_web":
            if data_reset_password := ResetPasswordModel.objects(
                token_web=token
            ).first():
                if (
                    data_reset_password.expired_at.replace(tzinfo=timezone.utc)
                    > created_at
                ):
                    return data_reset_password
                else:
                    data_reset_password.user.save()
                    data_reset_password.delete()
        if category == "by_token_email":
            if data_reset_password := ResetPasswordModel.objects(
                token_email=token
            ).first():
                if (
                    data_reset_password.expired_at.replace(tzinfo=timezone.utc)
                    > created_at
                ):
                    return data_reset_password
                else:
                    data_reset_password.user.save()
                    data_reset_password.delete()

    @staticmethod
    async def delete(category, **kwargs):
        user_id = kwargs.get("user_id")
        new_password = kwargs.get("new_password")
        created_at = kwargs.get("created_at")
        if category == "user_password_by_token_email":
            if user_data := UserModel.objects(id=user_id).first():
                if data_account_active := ResetPasswordModel.objects(
                    user=user_data
                ).first():
                    user_data.password = new_password
                    user_data.updated_at = created_at
                    user_data.save()
                    data_account_active.delete()
                    return data_account_active

    @staticmethod
    async def update(category, **kwargs):
        pass
