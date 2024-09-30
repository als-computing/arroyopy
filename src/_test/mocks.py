from als_arroyo.operator import AbstractOperator
from als_arroyo.publisher import AbstractPublisher


class MockOperator(AbstractOperator):
    def __init__(self, publisher: AbstractPublisher):
        super().__init__()
        self.publisher = publisher

    def run(self, data: str):
        self.publisher.publish(data)


class MockPublisher(AbstractPublisher):
    current_data = None

    async def publish(self, data):
        self.current_message = data
