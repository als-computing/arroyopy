import asyncio

import fakeredis.aioredis as redis
import pytest
import pytest_asyncio

from arroyo.redis import RedisListener, RedisPublisher

REDIS_CHANNEL_NAME = b"arroyo"

@pytest_asyncio.fixture
async def redis_client():
    client = await redis.FakeRedis()
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def redis_listener(operator_mock, redis_client):
    listener = RedisListener(
        redis_client=redis_client,
        redis_channel_name=REDIS_CHANNEL_NAME,
        operator=operator_mock)
    yield listener
    await listener.stop()


@pytest_asyncio.fixture
async def redis_publisher(operator_mock, redis_client, redis_channel_name):
    listener = RedisPublisher(
        operator=operator_mock,
        redis_channel_name=redis_channel_name)
    yield listener
    await listener.stop()


@pytest.mark.asyncio
async def test_from_client(operator_mock, redis_client):
    listener = await RedisListener.from_client(
                        redis_client=redis_client,
                        redis_channel_name=REDIS_CHANNEL_NAME,
                        operator=operator_mock)

    assert listener.redis_client == redis_client
    assert listener.redis_channel_name == REDIS_CHANNEL_NAME


@pytest.mark.asyncio
async def test_redis(redis_listener, redis_client, operator_mock):
    # Arrange
    async def send_messages():
        await asyncio.sleep(0.1)  # Give some time for the listener to start
        await redis_client.publish(REDIS_CHANNEL_NAME, b"message1")
        await asyncio.sleep(0.1)
        await redis_client.publish(REDIS_CHANNEL_NAME, b"message2")
        await asyncio.sleep(0.1)
        await redis_listener.stop()

    listener_task = asyncio.create_task(redis_listener.start())
    await send_messages()
    await listener_task
    operator_mock.process.assert_any_await(b"message1")  # Check operator run with first message
    operator_mock.process.assert_any_await(b"message2")  # Check operator run with second message
