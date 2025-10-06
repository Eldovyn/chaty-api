from .database import Database
from ..models import OtpEmailModel, UserModel


class OtpEmailDatabase(Database):
    @staticmethod
    async def insert(user_id, otp, created_at, expired_at):
        if data_user := UserModel.objects(id=user_id).first():
            if data_otp := OtpEmailModel.objects(user=data_user).first():
                data_otp.otp = otp
                data_otp.updated_at = int(created_at)
                data_otp.expired_at = int(expired_at)
                data_otp.save()
                return data_otp
            otp_email_data = OtpEmailModel(
                user=data_user,
                otp=otp,
                created_at=int(created_at),
                updated_at=int(created_at),
                expired_at=int(expired_at),
            )
            otp_email_data.save()
            return otp_email_data

    @staticmethod
    async def get(category, **kwargs):
        pass

    @staticmethod
    async def delete(category, **kwargs):
        pass

    @staticmethod
    async def update(category, **kwargs):
        pass
