"""
Unit - A container for operator, listeners, and publishers.

A Unit represents a complete processing unit in arroyo with:
- One operator that processes messages
- Any number of listeners (sources) that feed the operator
- Any number of publishers (sinks) that receive processed messages
"""
import asyncio
import logging
from typing import List, Optional

from .listener import Listener
from .operator import Operator
from .publisher import Publisher

logger = logging.getLogger(__name__)


class Unit:
    """
    A Unit encapsulates a complete arroyo processing pipeline.

    The Unit contains an operator and manages its associated listeners
    and publishers, providing lifecycle management for the entire pipeline.

    Attributes
    ----------
    name : str
        Unique identifier for this unit
    operator : Operator
        The operator that processes messages
    listeners : List[Listener]
        List of listeners feeding this unit
    publishers : List[Publisher]
        List of publishers receiving processed messages

    Example
    -------
    >>> operator = MyOperator()
    >>> listener = ZMQListener(operator, zmq_socket)
    >>> publisher = RedisPublisher(redis_client)
    >>>
    >>> unit = Unit(
    ...     name="my_pipeline",
    ...     operator=operator,
    ...     listeners=[listener],
    ...     publishers=[publisher]
    ... )
    >>> await unit.start()
    """

    def __init__(
        self,
        name: str,
        operator: Operator,
        listeners: Optional[List[Listener]] = None,
        publishers: Optional[List[Publisher]] = None,
    ):
        """
        Initialize a Unit.

        Parameters
        ----------
        name : str
            Unique identifier for this unit
        operator : Operator
            The operator instance that will process messages
        listeners : List[Listener], optional
            List of listener instances. Can also be added later via add_listener()
        publishers : List[Publisher], optional
            List of publisher instances. Can also be added later via add_publisher()
        """
        self.name = name
        self.operator = operator
        self._listeners: List[Listener] = listeners or []
        self._publishers: List[Publisher] = publishers or []
        self._running = False
        self._listener_tasks: List[asyncio.Task] = []

        # Wire up publishers to operator (sync operation)
        for publisher in self._publishers:
            self.operator.add_publisher(publisher)

    @property
    def listeners(self) -> List[Listener]:
        """Get the list of listeners for this unit."""
        return self._listeners

    @property
    def publishers(self) -> List[Publisher]:
        """Get the list of publishers for this unit."""
        return self._publishers

    async def add_listener(self, listener: Listener) -> None:
        """
        Add a listener to this unit.

        Parameters
        ----------
        listener : Listener
            Listener instance to add
        """
        self._listeners.append(listener)
        await self.operator.add_listener(listener)
        logger.info(f"Unit '{self.name}': Added listener {listener.__class__.__name__}")

    def add_publisher(self, publisher: Publisher) -> None:
        """
        Add a publisher to this unit.

        Parameters
        ----------
        publisher : Publisher
            Publisher instance to add
        """
        self._publishers.append(publisher)
        self.operator.add_publisher(publisher)
        logger.info(
            f"Unit '{self.name}': Added publisher {publisher.__class__.__name__}"
        )

    async def start(self) -> None:
        """
        Start the unit and begin processing.

        This starts all listeners and the operator's processing loop.
        """
        if self._running:
            logger.warning(f"Unit '{self.name}' is already running")
            return

        logger.info(
            f"Starting unit '{self.name}' with {len(self._listeners)} listener(s) "
            f"and {len(self._publishers)} publisher(s)"
        )

        self._running = True

        # Start the operator
        await self.operator.start()

        # Start all listeners as separate tasks
        for listener in self._listeners:
            task = asyncio.create_task(listener.start())
            self._listener_tasks.append(task)
            logger.info(f"Started listener: {listener.__class__.__name__}")

        # Wait for all listener tasks to complete
        if self._listener_tasks:
            await asyncio.gather(*self._listener_tasks)

    async def stop(self) -> None:
        """
        Stop the unit and all its components.

        This gracefully shuts down listeners and the operator.
        """
        if not self._running:
            logger.warning(f"Unit '{self.name}' is not running")
            return

        logger.info(f"Stopping unit '{self.name}'")

        self._running = False
        self.operator.stop_requested = True

        # Stop all listeners
        for listener in self._listeners:
            await listener.stop()

        logger.info(f"Unit '{self.name}' stopped")

    def __repr__(self) -> str:
        """String representation of the unit."""
        return (
            f"Unit(name='{self.name}', "
            f"operator={self.operator.__class__.__name__}, "
            f"listeners={len(self._listeners)}, "
            f"publishers={len(self._publishers)})"
        )
