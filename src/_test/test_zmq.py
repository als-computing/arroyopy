import pytest
from queue import Queue, Empty
import threading
import time
import zmq
import zmq.asyncio

from als_arroyo.zmq import ZMQListener
from als_arroyo.operator import AbstractOperator
from als_arroyo.publisher import AbstractPublisher


class TestOperator(AbstractOperator):
    def __init__(self, publisher: AbstractPublisher):
        super().__init__()
        self.publisher = publisher

    def run(self, data: str):
        self.publisher.publish(data)


class TestPublisher(AbstractPublisher):
    current_data = None

    async def publish(self, data):
        self.current_message = data


# Fixture to launch a ZMQ publisher that waits for test input to publish messages
@pytest.fixture(scope="function")
def zmq_publisher():
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5555")

    # Queue to receive messages from the test to publish
    message_queue = Queue()

    def publish():
        while True:
            try:
                # Block until a message is available, with a small timeout to allow shutdown
                message = message_queue.get(timeout=0.1)
                publisher.send_string(message)
            except Empty:
                continue

    # Start the publisher thread that will wait for messages to publish
    publisher_thread = threading.Thread(target=publish, daemon=True)
    publisher_thread.start()

    def send_message(message):
        """Function that test will call to send a message to the publisher."""
        message_queue.put(message)

    yield send_message  # Yield the function to the test

    # After the test is done, cleanup
    publisher.close()
    context.term()


def test_zmq(zmq_publisher):
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics

    publisher = TestPublisher()
    operator = TestOperator(publisher)

    listener = ZMQListener(operator, subscriber)
    listener.start()

    # Send a specific message via the publisher
    test_message = "Don't Panic!"
    zmq_publisher("test_message")
    time.sleep(0.1)
    result_message = publisher.current_message = test_message
    assert result_message == test_message


def test_factories():
    ...
