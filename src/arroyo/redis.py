import asyncio
import logging

from redis.asyncio.client import Redis

from .listener import Listener
from .operator import Operator

logger = logging.getLogger("arroyo.zmq")


class RedisListener(Listener):

    def __init__(
            self,
            redis_client: Redis,
            redis_channel_name: str,
            operator: Operator):

        self.stop_requested = False
        self.redis_client: Redis = redis_client
        self.redis_channel_name = redis_channel_name
        self.operator = operator

    @classmethod
    async def from_client(
            cls,
            redis_client: Redis,
            redis_channel_name: str,
            operator: Operator):
        return RedisListener(redis_client, redis_channel_name, operator)

    async def start(self):
        logger.info("Listener started")
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.redis_channel_name)
        # Listen for messages in the subscribed channel
        while True:
            if self.stop_requested:
                return
            # get_message blocks until timeout, returning None if no message in that time
            raw_msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if raw_msg is None:
                continue
            msg = raw_msg['data']
            if logger.getEffectiveLevel() == logging.DEBUG:
                logger.debug(f"{msg=}")
            await self.operator.process(msg)

    async def stop(self):
        self.stop_requested = True
        await self.redis_client.aclose()


class RedisPublisher:

    def __init__(
            self,
            redis_client: Redis,
            redis_channel_name: str):

        self.redis_client: Redis = redis_client
        self.redis_channel_name = redis_channel_name

    @classmethod
    async def from_client(
            cls,
            redis_client: Redis,
            redis_channel_name: str):
        return RedisPublisher(redis_client, redis_channel_name)

    async def publish(self, message):
        await self.redis_client.publish(self.redis_channel_name, message)
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug(f"Published {message=}")
