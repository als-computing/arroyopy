from abc import ABC, abstractmethod

from .publisher import AbstractPublisher


class AbstractOperator(ABC):

    publisher: AbstractPublisher

    @abstractmethod
    async def run(self, message):
        pass
