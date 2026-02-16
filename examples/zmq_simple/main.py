import asyncio

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

    async def start(self, address="tcp://127.0.0.1:5556"):
        async with ZMQSource(address) as socket:
            while True:
                for i in range(10):
                    message = f"Message {i}"
                    await socket.socket.send_string(message)
                    print(f"Sent: {message}")
                await asyncio.sleep(1)


if __name__ == "__main__":
    source = ZMQSource("tcp://127.0.0.1:5556")
    asyncio.run(source.start())
