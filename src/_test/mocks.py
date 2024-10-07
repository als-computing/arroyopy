from arroyo.operator import AbstractOperator
from arroyo.publisher import AbstractPublisher
from arroyo.schemas import Message


class MockOperator(AbstractOperator):
    def __init__(self, publisher: AbstractPublisher):
        super().__init__()
        self.publisher = publisher

    def process(self, data: Message) -> None:
        self.publisher.publish(data)


class MockPublisher(AbstractPublisher):
    current_data = None

    async def publish(self, message: Message) -> None:
        self.current_message = message
