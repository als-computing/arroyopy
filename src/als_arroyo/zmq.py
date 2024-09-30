import logging

import zmq
import zmq.asyncio

from .listener import AbstractListener
from .operator import AbstractOperator


logger = logging.getLogger("arroyo.zmq")


class ZMQListener(AbstractListener):

    def __init__(
            self,
            operator: AbstractOperator,
            zmq_socket: zmq.Socket):

        self.operator = operator
        self.zmq_socket = zmq_socket

    @classmethod
    def from_socket(cls, zmq_socket: zmq.Socket):
        """Construct a ZMQListenr using a provided socket. Gives 
        callers the ability to customize the ZMQ soket

        Parameters
        ----------
        zmq_socket : zmq.Socket
           provided socket

        Returns
        -------
        ZMQListner
            new ZMQListner
        """
        return ZMQListener(zmq_socket)


    async def start(self):
        print("foo")
        logger.info("Listener started")
        while True:
            raw_msg = await self.zmq_socket.recv_multipart()
            msg = await self.parser.parse(raw_msg)
            if logger.getEffectiveLevel() == logging.DEBUG:
                logger.debug(f"{msg=}")
            await self.operator.run(msg)

    async def stop(self):
        self.zmq_socket.close()
        self.zmq_socket.context.term()
