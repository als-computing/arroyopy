import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import List

from .listener import Listener
from .publisher import Publisher
from .schemas import Message
from .telemetry import get_metrics_tracker

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
        await listener.start(self.listener_queue)

    def remove_listener(self, listener: Listener) -> None:  # noqa
        self.listeners.remove(listener)

    def add_publisher(self, publisher: Publisher) -> None:
        self.publishers.append(publisher)

    def remove_publisher(self, publisher: Publisher) -> None:
        self.publishers.remove(publisher)

    async def notify(self, message: Message) -> None:
        await self.listener_queue.put(message)

    async def publish(self, message: Message) -> None:
        for publisher in self.publishers:
            await publisher.publish(message)

    async def start(self):
        # Process messages from the queue
        metrics_tracker = get_metrics_tracker()
        operator_type = self.__class__.__name__

        while True:
            if self.stop_requested:
                logger.info("Stopping operator...")
                for listener in self.listeners:
                    await listener.stop()
                break
            message = await self.listener_queue.get()

            # Track processing time
            start_time = time.perf_counter()
            processed_message = await self.process(message)
            duration = time.perf_counter() - start_time

            # Record metrics
            metrics_tracker.record_processing_time(operator_type, duration)

            await self.publish(processed_message)
