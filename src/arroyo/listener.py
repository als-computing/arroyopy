from abc import ABC, abstractmethod

from .operator import AbstractOperator


class AbstractListener(ABC):

    operator: AbstractOperator

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
