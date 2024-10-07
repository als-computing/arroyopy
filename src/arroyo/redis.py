import asyncio
import logging


from redis.asyncio import Redis


from .listener import AbstractListener
from .operator import AbstractOperator


logger = logging.getLogger("arroyo.zmq")

REDIS_CHANNEL_NAME = b"arroyo"


class RedisListener(AbstractListener):

    def __init__(
            self,
            operator: AbstractOperator,
            redis_client: Redis,
            redis_pubsub):

        self.operator = operator
        self.stop_requested = False
        self.redis_client: Redis = redis_client
        self.redis_pub_sub = redis_pubsub

    @classmethod
    async def from_client(
            cls,
            operator: AbstractOperator,
            redis_client: Redis,
            redis_pub_sub):
        return RedisListener(operator, redis_client, redis_pub_sub)

    async def start(self):
        logger.info("Listener started")
        while True:
            if self.stop_requested:
                return
            # get_message blocks until timeout, returning None if no message in that time
            raw_msg = await self.redis_pub_sub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if raw_msg is None:
                continue
            msg = raw_msg['data']
            if logger.getEffectiveLevel() == logging.DEBUG:
                logger.debug(f"{msg=}")
            await self.operator.process(msg)     

    async def stop(self):
        self.stop_requested = True
        self.redis_pub_sub.aclose()
        self.redis_client.aclose()
