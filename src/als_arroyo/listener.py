from abc import ABC, abstractmethod

from .message import AbstractMessageParser
from .operator import AbstractOperator


class AbstractListener(ABC):

    operator: AbstractOperator
    parser: AbstractMessageParser

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
