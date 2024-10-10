from abc import ABC, abstractmethod
from typing import List

from .listener import Listener
from .publisher import Publisher
from .schemas import Message


class Operator(ABC):
    listeners: List[Listener] = []
    publishers: List[Publisher] = []

    @abstractmethod
    async def process(self, message: Message) -> None:
        pass

    def add_listener(self, listener: Listener) -> None: # noqa
        self.listeners.append(listener)

    def remove_listener(self, listener: Listener) -> None: # noqa
        self.listeners.remove(listener)

    def add_publisher(self, publisher: Publisher) -> None:
        self.publishers.append(publisher)

    def remove_publisher(self, publisher: Publisher) -> None:
        self.publishers.remove(publisher)

    async def publish(self, message: Message) -> None:
        for publisher in self.publishers:
            await publisher.publish(message)
