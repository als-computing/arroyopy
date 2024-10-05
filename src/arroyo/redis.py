import asyncio
import logging


from redis.asyncio import Redis


from .listener import AbstractListener
from .schemas import AbstractMessageParser
from .operator import AbstractOperator


logger = logging.getLogger("arroyo.zmq")

REDIS_CHANNEL_NAME = b"arroyo"


class RedisListener(AbstractListener):

    def __init__(
            self,
            operator: AbstractOperator,
            message_parser: AbstractMessageParser,
            redis_client: Redis,
            redis_pubsub):

        self.operator = operator
        self.message_parser = message_parser
        self.redis_client: Redis = redis_client
        self.redis_pub_sub = redis_pubsub

    @classmethod
    async def from_client(
            cls,
            operator: AbstractOperator,
            message_parser: AbstractMessageParser,
            redis_client: Redis,
            redis_pub_sub):
        return RedisListener(operator, message_parser, redis_client, redis_pub_sub)

    async def start(self):
        logger.info("Listener started")
        while True:
            # get_message blocks until timeout, returning None if no message in that time
            raw_msg = await self.redis_pub_sub.get_message(ignore_subscribe_messages=True, timeout=20.0)
            if raw_msg is None:
                continue
            msg = await self.parser.parse(raw_msg['data'])
            if logger.getEffectiveLevel() == logging.DEBUG:
                logger.debug(f"{msg=}")
            await self.operator.run(msg)

    async def stop(self):
        self.pub_sub.close()
        self.redis_client.close()
