import asyncio
from abc import ABC, abstractmethod


class Listener(ABC):
    message_queue: asyncio.Queue

    @abstractmethod
    async def start(self, message_queue) -> None:
        self.message_queue = message_queue

    @abstractmethod
    async def stop(self) -> None:
        pass
