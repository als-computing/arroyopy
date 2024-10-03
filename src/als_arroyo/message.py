from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List


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
    async def parse(self, message: List[bytes]):
        pass
