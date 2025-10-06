from abc import ABC, abstractmethod


class Database(ABC):
    @abstractmethod
    async def insert(**kwargs):
        pass

    @abstractmethod
    async def update(**kwargs):
        pass

    @abstractmethod
    async def delete(**kwargs):
        pass

    @abstractmethod
    async def get(**kwargs):
        pass
