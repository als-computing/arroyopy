from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .schemas import Message

T = TypeVar('T', bound=Message)

class Publisher(ABC, Generic[T]):

    @abstractmethod
    async def publish(self, message: Message) -> None:
        pass
