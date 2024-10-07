import asyncio
import logging

import zmq
import zmq.asyncio

from .listener import AbstractListener
from .operator import AbstractOperator


logger = logging.getLogger("arroyo.zmq")


class ZMQListener(AbstractListener):

    stop_signal: bool = False

    def __init__(
            self,
            operator: AbstractOperator,
            zmq_socket: zmq.Socket):
        self.stop_requested = False
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
        logger.info("Listener started")
        # timeout after 100 milliseconds so we can be stopped if requested
        self.zmq_socket.setsockopt(zmq.RCVTIMEO, 100)
        while True:
            if self.stop_requested:
                return
            try:
                msg = await self.zmq_socket.recv()
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug(f"{msg=}")
                await self.operator.process(msg)
            except zmq.Again:
                # no message occured within the timeout period
                pass
            except asyncio.exceptions.CancelledError:
                # in case this is being done in a asyncio.create_task call
                pass
  

    async def stop(self):
        self.stop_requested = True
        self.zmq_socket.close()
        self.zmq_socket.context.term()
