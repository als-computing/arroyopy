from abc import ABC, abstractmethod

from .operator import Operator


class Listener(ABC):

    operator: Operator

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
