from abc import ABC, abstractmethod

from .publisher import AbstractPublisher
from .message import Event


class AbstractOperator(ABC):

    publisher: AbstractPublisher

    @abstractmethod
    async def Event(self, event: Event) -> None:
        pass
