from arroyo.operator import Operator
from arroyo.publisher import Publisher
from arroyo.schemas import Message


class MockOperator(Operator):
    def __init__(self, publisher: Publisher):
        super().__init__()
        self.publisher = publisher

    def process(self, data: Message) -> None:
        self.publisher.publish(data)


class MockPublisher(Publisher):
    current_data = None

    async def publish(self, message: Message) -> None:
        self.current_message = message
