"""
Simple console sink that subscribes to ZMQ and prints messages.

Run this to see the output from the pipeline.
"""
import asyncio
import logging

import zmq
import zmq.asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_sink(address: str = "tcp://127.0.0.1:5556"):
    """
    Subscribe to ZMQ socket and print messages to console.

    Parameters
    ----------
    address : str
        ZMQ address to subscribe to
    """
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(address)
    socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    logger.info(f"Subscribing to {address}")
    logger.info("Waiting for messages... (Ctrl+C to stop)")
    print("=" * 60)

    try:
        msg_count = 0
        while True:
            message = await socket.recv()
            msg_count += 1

            # Decode and print
            try:
                text = message.decode("utf-8")
            except UnicodeDecodeError:
                text = f"<binary: {len(message)} bytes>"

            print(f"[{msg_count}] {text}")

    except KeyboardInterrupt:
        logger.info(f"\nReceived {msg_count} messages total")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Simple console sink for arroyopy demo"
    )
    parser.add_argument(
        "--address",
        default="tcp://127.0.0.1:5556",
        help="ZMQ address to subscribe to (default: tcp://127.0.0.1:5556)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_sink(args.address))
    except KeyboardInterrupt:
        pass
