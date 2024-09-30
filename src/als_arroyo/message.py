from abc import ABC, abstractmethod
from pydantic import BaseModel


class Message(BaseModel):
    pass


class Start(Message):
    data: dict


class Stop(Message):
    data: dict


class Event(Message):
    metadata: dict
    payload: bytes


class AbstractMessageParser(ABC):

    @abstractmethod
    async def parse(self, message: bytes):
        pass
