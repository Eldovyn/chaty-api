from abc import ABC, abstractmethod


class Token(ABC):
    @abstractmethod
    async def insert(**kwargs):
        pass

    @abstractmethod
    async def get(**kwargs):
        pass
