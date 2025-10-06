from abc import ABC, abstractmethod


class SerializerInterface(ABC):

    @abstractmethod
    def serialize(self, **kwargs):
        pass
