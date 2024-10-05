from abc import ABC, abstractmethod

from .schemas import Message


class AbstractPublisher(ABC):

    @abstractmethod
    async def publish(self, message: Message) -> None:
        pass
