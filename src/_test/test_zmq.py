import asyncio
from queue import Queue, Empty
import threading

import pytest
import pytest_asyncio
import zmq
import zmq.asyncio


from als_arroyo.zmq import ZMQListener
from .mocks import MockOperator, MockPublisher


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

@pytest.fixture
async def zmq_subscriber()
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics
    yield subscriber
    subscriber.disconnect()

@pytest.mark.asyncio
async def test_zmq(zmq_publisher, zmq_subscriber):
    # this uses a 
    publisher = MockPublisher()
    operator = MockOperator(publisher)

    listener = ZMQListener(operator, zmq_subscriber)
    await listener.start()

    # Send a specific message via the publisher
    test_message = "Don't Panic!"
    zmq_publisher(test_message)
    asyncio.sleep(0.1)
    result_message = publisher.current_message = test_message
    assert result_message == test_message

    test_message = "Don't Panic! 2"
    zmq_publisher(test_message)
    asyncio.sleep(0.1)
    result_message = publisher.current_message = test_message
    assert result_message == test_message


@pytest.mark.asyncio
def test_from_socket(zmq_subscriber):
    # zmq_listener = ZMQListener()
    pass
