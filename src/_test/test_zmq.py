import asyncio
from queue import Queue, Empty
import threading

import pytest
import pytest_asyncio
import zmq
import zmq.asyncio


from arroyo.zmq import ZMQListener
from .mocks import MockOperator, MockPublisher


# Fixture to launch a ZMQ publisher that waits for test input to publish messages
@pytest_asyncio.fixture
async def zmq_publisher():     
    class TestPublisher():

        def __init__(self):
            self.context = zmq.asyncio.Context()
            self.socket = self.context.socket(zmq.PUB)

        def start(self):
            self.socket.bind("tcp://127.0.0.1:5555")

        async def send_message(self, message):
            """Function that test will call to send a message to the publisher."""
            await self.socket.send(message)

        def stop(self):
            # After the test is done, cleanup
            self.socket.close()
            self.context.term()
    return TestPublisher()

@pytest_asyncio.fixture
async def zmq_subscriber():
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5555")
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics
    yield subscriber
    subscriber.disconnect()


@pytest_asyncio.fixture
async def zmq_listener(operator_mock, zmq_subscriber):
    return ZMQListener(operator_mock, zmq_subscriber)


@pytest.mark.asyncio
async def test_zmq(zmq_listener, zmq_publisher, operator_mock):

    async def send_messages():
        await asyncio.sleep(0.2)
        await zmq_publisher.send_message(b"message1")
        await asyncio.sleep(0.2)
        await zmq_publisher.send_message(b"message2")
        await asyncio.sleep(0.2)
        await zmq_listener.stop()

    zmq_publisher.start()
    listener_task = asyncio.create_task(zmq_listener.start())
    await send_messages()
    await listener_task
    operator_mock.process.assert_any_await(b"message1")  # Check operator run with first message
    operator_mock.process.assert_any_await(b"message2")  # Check operator run with second messag


@pytest.mark.asyncio
def test_from_socket(zmq_subscriber):
    # zmq_listener = ZMQListener()
    pass
