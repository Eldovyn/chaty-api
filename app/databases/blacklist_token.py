from .database import Database
from ..models import BlacklistTokenModel, UserModel


class BlacklistTokenDatabase(Database):
    @staticmethod
    async def insert(user_id, created_at):
        if user_data := UserModel.objects(id=user_id).first():
            data_token = BlacklistTokenModel(user=user_data, created_at=created_at)
            data_token.save()
            return data_token

    @staticmethod
    async def get(category, **kwargs):
        pass

    @staticmethod
    async def delete(category, **kwargs):
        pass

    @staticmethod
    async def update(category, **kwargs):
        pass
