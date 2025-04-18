from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Listener(ABC, Generic[T]):
    def __init__(self, operator: T):
        super().__init__()
        self.operator = operator

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
