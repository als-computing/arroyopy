from abc import ABC, abstractmethod
from typing import List

from .publisher import AbstractPublisher
from .schemas import Message


class AbstractOperator(ABC):

    publisher: List[AbstractPublisher] = []

    @abstractmethod
    async def process(self, message: Message) -> None:
        pass

    def add_publisher(self, publisher: AbstractPublisher) -> None:
        self.publisher.append(publisher)

    def remove_publisher(self, publisher: AbstractPublisher) -> None:
        self.publisher.remove(publisher)

    async def publish(self, message: Message) -> None:
        for publisher in self.publisher:
            await publisher.publish(message)
