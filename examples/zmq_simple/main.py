import zmq
import zmq.asyncio

"""
This is almost a Hello World example for ZMQ. It sets up a ZMQ socket and publishes numbers to it.

"""


class ZMQSource:
    def __init__(self, address):
        self.address = address
        self.stop_requested = False

    async def __aenter__(self):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(self.address)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()
        self.context.term()

    async def start():
        pass

    async def start_zmq(address="tcp://127.0.0.1:5555"):
        async with ZMQSource(address) as socket:
            while True:
                message = await socket.recv()
                print(f"Received: {message}")
                await socket.send(b"Message received")


# if __name__ == "__main__":
#     asyncio.run(start_zmq())
