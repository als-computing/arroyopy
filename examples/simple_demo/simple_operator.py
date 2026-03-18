"""
Simple operator for demonstration purposes.

This operator receives messages, transforms them slightly, and passes them on.
"""
import logging
from typing import Any

from arroyopy.operator import Operator

logger = logging.getLogger(__name__)


class SimpleOperator(Operator):
    """
    A simple demonstration operator that transforms messages.

    This operator:
    - Receives messages from listeners
    - Adds a processing timestamp and counter
    - Publishes to all registered publishers
    """

    def __init__(self, prefix: str = "Processed", **kwargs):
        """
        Initialize the operator.

        Parameters
        ----------
        prefix : str
            Prefix to add to processed messages
        """
        super().__init__(**kwargs)
        self.prefix = prefix
        self.message_count = 0
        logger.info(f"SimpleOperator initialized with prefix='{prefix}'")

    async def process(self, data: Any) -> None:
        """
        Process incoming data.

        Parameters
        ----------
        data : Any
            The data to process (typically bytes from ZMQ)
        """
        self.message_count += 1

        # Decode if bytes
        if isinstance(data, bytes):
            message = data.decode("utf-8")
        else:
            message = str(data)

        # Transform the message
        processed = f"{self.prefix} #{self.message_count}: {message}"

        logger.info(f"Processing: {message} -> {processed}")

        # Publish to all publishers
        await self.publish(processed.encode("utf-8"))

    async def start(self) -> None:
        """Called when the operator starts."""
        logger.info("SimpleOperator started")
        self.message_count = 0

    async def stop(self) -> None:
        """Called when the operator stops."""
        logger.info(f"SimpleOperator stopped. Processed {self.message_count} messages")
