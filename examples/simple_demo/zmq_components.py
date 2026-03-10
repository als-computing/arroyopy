"""
ZMQ components with address-based configuration for the simple demo.

These wrappers make it easier to configure ZMQ listeners and publishers
using addresses in YAML config files.
"""
import zmq
import zmq.asyncio

from arroyopy.operator import Operator
from arroyopy.publisher import Publisher
from arroyopy.zmq import ZMQListener


class SimpleZMQListener(ZMQListener):
    """
    ZMQ Listener that can be configured with an address string.

    This wraps the base ZMQListener to handle socket creation
    from configuration.
    """

    def __init__(self, operator: Operator, address: str, socket_type: str = "SUB"):
        """
        Initialize a ZMQ listener with address-based configuration.

        Parameters
        ----------
        operator : Operator
            The operator to process received messages
        address : str
            ZMQ address (e.g., 'tcp://127.0.0.1:5555')
        socket_type : str
            ZMQ socket type ('SUB', 'PULL', etc.)
        """
        context = zmq.asyncio.Context()

        # Map string socket type to zmq constant
        socket_types = {
            "SUB": zmq.SUB,
            "PULL": zmq.PULL,
            "PAIR": zmq.PAIR,
        }

        zmq_socket = context.socket(socket_types.get(socket_type, zmq.SUB))
        zmq_socket.connect(address)

        # Subscribe to all messages if SUB socket
        if socket_type == "SUB":
            zmq_socket.setsockopt(zmq.SUBSCRIBE, b"")

        super().__init__(operator, zmq_socket)
        self.address = address


class SimpleZMQPublisher(Publisher):
    """
    ZMQ Publisher that can be configured with an address string.
    """

    def __init__(self, address: str, socket_type: str = "PUB"):
        """
        Initialize a ZMQ publisher with address-based configuration.

        Parameters
        ----------
        address : str
            ZMQ address (e.g., 'tcp://127.0.0.1:5556')
        socket_type : str
            ZMQ socket type ('PUB', 'PUSH', etc.)
        """
        self.address = address
        self.socket_type = socket_type
        self.context = zmq.asyncio.Context()

        # Map string socket type to zmq constant
        socket_types = {
            "PUB": zmq.PUB,
            "PUSH": zmq.PUSH,
            "PAIR": zmq.PAIR,
        }

        self.socket = self.context.socket(socket_types.get(socket_type, zmq.PUB))
        self.socket.bind(address)

    async def publish(self, data):
        """
        Publish data to the ZMQ socket.

        Parameters
        ----------
        data : bytes
            Data to publish
        """
        await self.socket.send(data)

    async def stop(self):
        """Clean up the socket and context."""
        self.socket.close()
        self.context.term()
