from abc import ABC, abstractmethod


class AbstractPublisher(ABC):

    @abstractmethod
    async def publish(self, data):
        pass
