import asyncio
import logging

import typer

from arroyopy import Operator, Publisher
from arroyopy.otlp import setup_telemetry
from arroyopy.zmq import ZMQListener, setup_pub_socket

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger("data_watcher")


def setup_logging(log_level: str = "INFO"):
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False  # Prevent duplication through root logger


# -----------------------------------------------------------------------------
# CLI App
# -----------------------------------------------------------------------------
app = typer.Typer(help="Watch a directory and publish new .gb files to Redis.")


class PrintingOperator(Operator):
    def __init__(self, publisher: Publisher):
        self.publisher = publisher

    async def process(self, message):
        logger.info(f"Processing message: {message}")
        await self.publisher.publish(message)


class NullPublisher(Publisher):
    async def publish(self, message):
        logger.debug(f"NullPublisher: {message} - No action taken.")


@app.command()
def main(
    zmq_publish_endpoint: str = typer.Option(
        "tcp://localhost:5556", help="ZMQ publisher endpoint"
    ),
    log_level: str = typer.Option(
        "INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    ),
):
    setup_logging(log_level)

    # Initialize OpenTelemetry
    logger.info("Initializing OpenTelemetry...")
    setup_telemetry(service_name="zmq-listener")

    socket = setup_pub_socket(zmq_publish_endpoint)
    publisher = NullPublisher()
    logger.info("Using default null publisher")

    operator = PrintingOperator(publisher)
    listener = ZMQListener.from_socket(operator, socket)

    try:
        asyncio.run(listener.start())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        asyncio.run(listener.stop())
        logger.info("Listener stopped successfully")


if __name__ == "__main__":
    app()
