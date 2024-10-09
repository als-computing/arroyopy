from abc import ABC, abstractmethod
from typing import List

from .publisher import Publisher
from .schemas import Message


class Operator(ABC):

    publisher: List[Publisher] = []

    @abstractmethod
    async def process(self, message: Message) -> None:
        pass

    def add_publisher(self, publisher: Publisher) -> None:
        self.publisher.append(publisher)

    def remove_publisher(self, publisher: Publisher) -> None:
        self.publisher.remove(publisher)

    async def publish(self, message: Message) -> None:
        for publisher in self.publisher:
            await publisher.publish(message)
