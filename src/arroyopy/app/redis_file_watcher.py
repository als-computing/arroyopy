import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from arroyopy import Operator, Publisher
from arroyopy.files import FileWatcherListener
from arroyopy.redis import RedisPublisher

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


class FileWatcherOperator(Operator):
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
    directory: Path = typer.Argument(..., help="Directory to watch for new files"),
    redis_host: Optional[str] = typer.Option(None, help="Redis host"),
    redis_port: Optional[int] = typer.Option(None, help="Redis port"),
    log_level: str = typer.Option(
        "INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)"
    ),
):
    setup_logging(log_level)

    loop = asyncio.get_event_loop()

    if redis_host:
        publisher = RedisPublisher.from_client(redis_host, redis_port)
        logger.info(
            f"Using Redis publisher with host {redis_host} and port {redis_port}"
        )
    else:
        publisher = NullPublisher()
        logger.info("Using default null publisher")

    operator = FileWatcherOperator(publisher)
    listener = FileWatcherListener(str(directory), operator)
    loop.run_until_complete(listener.start())


if __name__ == "__main__":
    app()
