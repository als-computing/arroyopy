import asyncio
from abc import ABC, abstractmethod


T = TypeVar('T')

class Listener(ABC, Generic[T]):

    def __init__(self, operator: T):
        super().__init__()
        self.operator = operator

    @abstractmethod
    async def start(self, message_queue) -> None:
        self.message_queue = message_queue

    @abstractmethod
    async def stop(self) -> None:
        pass
