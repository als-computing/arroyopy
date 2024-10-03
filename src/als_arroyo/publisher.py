from abc import ABC, abstractmethod

from .message import Message


class AbstractPublisher(ABC):

    @abstractmethod
    async def publish(self, message: Message) -> None:
        pass
