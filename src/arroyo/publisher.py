from abc import ABC, abstractmethod

from .schemas import Message


class Publisher(ABC):
    @abstractmethod
    async def publish(self, message: Message) -> None:
        pass
