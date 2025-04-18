import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List

from .listener import Listener
from .publisher import Publisher
from .schemas import Message

logger = logging.getLogger(__name__)


class Operator(ABC):
    listeners: List[Listener] = []
    publishers: List[Publisher] = []
    stop_requested: bool = False

    def __init__(self):
        self.listener_queue = asyncio.Queue()

    @abstractmethod
    async def process(self, message: Message) -> None:
        pass

    async def add_listener(self, listener: Listener) -> None:  # noqa
        self.listeners.append(listener)
        await listener.start()
    
    def remove_listener(self, listener: Listener) -> None:  # noqa
        self.listeners.remove(listener)

    def add_publisher(self, publisher: Publisher) -> None:
        self.publishers.append(publisher)

    def remove_publisher(self, publisher: Publisher) -> None:
        self.publishers.remove(publisher)

    async def publish(self, message: Message) -> None:
        for publisher in self.publishers:
            await publisher.publish(message)

    async def start(self):
        # Process messages from the queue
        while True:
            if self.stop_requested:
                logger.info("Stopping operator...")
                for listener in self.listeners:
                    await listener.stop()
                break
            message = await self.queue.get()
            processed_message = await self.process(message)
            await self.publish(processed_message)
