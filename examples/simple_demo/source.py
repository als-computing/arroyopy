"""
Simple data source that publishes test messages to ZMQ.

Run this to generate test data for the pipeline.
"""
import asyncio
import logging

import zmq
import zmq.asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_source(
    address: str = "tcp://127.0.0.1:5555", interval: float = 1.0, count: int = 10
):
    """
    Publish test messages to ZMQ socket.

    Parameters
    ----------
    address : str
        ZMQ address to publish to
    interval : float
        Seconds between messages
    count : int
        Number of messages to send (0 = infinite)
    """
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(address)

    logger.info(f"Publishing to {address}")
    logger.info(
        f"Sending {count if count > 0 else 'infinite'} messages at {interval}s intervals"
    )

    # Give subscribers time to connect
    await asyncio.sleep(0.5)

    try:
        msg_num = 0
        while count == 0 or msg_num < count:
            msg_num += 1
            message = f"Message {msg_num}"

            await socket.send_string(message)
            logger.info(f"Sent: {message}")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        socket.close()
        context.term()
        logger.info(f"Sent {msg_num} messages total")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple data source for arroyopy demo")
    parser.add_argument(
        "--address",
        default="tcp://127.0.0.1:5555",
        help="ZMQ address to publish to (default: tcp://127.0.0.1:5555)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between messages (default: 1.0)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of messages to send, 0 for infinite (default: 10)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_source(args.address, args.interval, args.count))
    except KeyboardInterrupt:
        logger.info("Stopped by user")
