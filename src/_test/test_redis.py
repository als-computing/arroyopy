import asyncio

import fakeredis.aioredis as fakeredis
import pytest
import pytest_asyncio

from als_arroyo.redis import RedisListener, REDIS_CHANNEL_NAME


@pytest_asyncio.fixture
async def redis_client():
    client = await fakeredis.FakeRedis() 
    yield client
    await client.wait_closed()


@pytest_asyncio.fixture
async def redis_pub_sub(redis_client):
    redis_pub_sub = redis_client.pubsub()
    await redis_pub_sub.subscribe(REDIS_CHANNEL_NAME)
    yield redis_pub_sub
    await redis_pub_sub.close()


@pytest_asyncio.fixture
async def redis_listener(operator_mock, message_parser_mock, redis_client, redis_pub_sub):
    listener = RedisListener(
        operator=operator_mock,
        message_parser=message_parser_mock,
        redis_client=redis_client,
        redis_pubsub=redis_pub_sub)

    listener.parser = message_parser_mock  # Set the parser mock in the listener
    await redis_pub_sub.subscribe(REDIS_CHANNEL_NAME)  # Subscribe to the channel
    yield listener
    await listener.stop()


@pytest.mark.asyncio
async def test_from_client(operator_mock, message_parser_mock, redis_client, redis_pub_sub):
    listener = await RedisListener.from_client(
                        operator=operator_mock,
                        message_parser=message_parser_mock,
                        redis_client=redis_client,
                        redis_pub_sub=redis_pub_sub)

    assert listener.operator == operator_mock
    assert listener.redis_client == redis_client
    assert listener.redis_pub_sub == redis_pub_sub
    assert REDIS_CHANNEL_NAME in redis_pub_sub.channels.keys()  # Ensure the channel was subscribed


@pytest.mark.asyncio
async def test_start(redis_listener, redis_pub_sub, redis_client, operator_mock):
    # Arrange
    async def send_messages():
        await asyncio.sleep(0.1)  # Give some time for the listener to start
        await redis_client.publish(REDIS_CHANNEL_NAME, b"message1")
        await asyncio.sleep(0.1)
        await redis_client.publish(REDIS_CHANNEL_NAME, b"message2")
        await asyncio.sleep(0.1)
        await redis_pub_sub.unsubscribe(REDIS_CHANNEL_NAME)  # Unsubscribe to stop the listener

    # Mock parser to decode bytes to string
    redis_listener.parser.parse.side_effect = lambda x: x.decode() if x else None
    asyncio.create_task(redis_listener.start())

    await send_messages()
    # Assert
    redis_listener.parser.parse.assert_any_call(b"message1")  # Check first parse
    redis_listener.parser.parse.assert_any_call(b"message2")  # Check second parse
    operator_mock.run.assert_any_await("message1")  # Check operator run with first message
    operator_mock.run.assert_any_await("message2")  # Check operator run with second message


@pytest.mark.asyncio
async def test_stop(redis_listener, pub_sub, redis_client):
    # Act
    await redis_listener.stop()

    # Assert
    assert not pub_sub.channels  # Check that all channels are unsubscribed
    await redis_client.wait_closed()  # Ensure the connection is closed properly
