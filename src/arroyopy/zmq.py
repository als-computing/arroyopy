import asyncio
import logging
import os
import time

import zmq
import zmq.asyncio

# from opentelemetry import trace
from opentelemetry.metrics import Observation
from opentelemetry.trace import Status, StatusCode

from .listener import Listener
from .operator import Operator
from .otlp import get_meter, get_tracer

logger = logging.getLogger("arroyo.zmq")
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# Get process identifier for multi-process metrics
PROCESS_ID = os.getpid()

# Create metrics
messages_received_counter = meter.create_counter(
    "zmq.messages.received",
    description="Total number of messages received",
    unit="1",
)

messages_processed_counter = meter.create_counter(
    "zmq.messages.processed",
    description="Total number of messages successfully processed",
    unit="1",
)

messages_failed_counter = meter.create_counter(
    "zmq.messages.failed",
    description="Total number of messages that failed processing",
    unit="1",
)

message_size_histogram = meter.create_histogram(
    "zmq.message.size",
    description="Distribution of message sizes in bytes",
    unit="bytes",
)

processing_duration_histogram = meter.create_histogram(
    "zmq.message.processing.duration",
    description="Message processing duration",
    unit="seconds",
)

# Track active listeners count for this process
_active_listeners_count = 0


def _get_active_listeners(options):
    """Callback for observable gauge - reports 1 if any listeners are active in this process"""
    yield Observation(
        1 if _active_listeners_count > 0 else 0, {"process_id": str(PROCESS_ID)}
    )


active_listeners_gauge = meter.create_observable_gauge(
    "zmq.listeners.active",
    callbacks=[_get_active_listeners],
    description="Number of active ZMQ listeners",
    unit="1",
)


class ZMQListener(Listener):
    stop_signal: bool = False

    def __init__(self, operator: Operator, zmq_socket: zmq.Socket):
        self.stop_requested = False
        self.operator = operator
        self.zmq_socket = zmq_socket
        self._active = False

    @classmethod
    def from_socket(cls, operator: Operator, zmq_socket: zmq.Socket):
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
        return ZMQListener(operator, zmq_socket)

    async def start(self):
        global _active_listeners_count

        with tracer.start_as_current_span("zmq_listener.start") as span:
            logger.info("Listener started")
            span.set_attribute("listener.type", "zmq")

            # Mark this listener as active
            if not self._active:
                _active_listeners_count += 1
                self._active = True

            # timeout after 100 milliseconds so we can be stopped if requested
            self.zmq_socket.setsockopt(zmq.RCVTIMEO, 100)

            message_count = 0
            while True:
                if self.stop_requested:
                    span.set_attribute("listener.messages_processed", message_count)
                    span.set_attribute("listener.stopped_by_request", True)
                    if self._active:
                        _active_listeners_count -= 1
                        self._active = False
                    return
                try:
                    with tracer.start_as_current_span(
                        "zmq_listener.receive_message"
                    ) as msg_span:
                        msg = await self.zmq_socket.recv()
                        msg_size = len(msg)

                        # Record metrics
                        messages_received_counter.add(1, {"listener.type": "zmq"})
                        message_size_histogram.record(
                            msg_size, {"listener.type": "zmq"}
                        )

                        msg_span.set_attribute("message.size_bytes", msg_size)

                        if logger.getEffectiveLevel() == logging.DEBUG:
                            logger.debug(f"{msg=}")

                        message_count += 1
                        msg_span.set_attribute("message.count", message_count)

                        # Track processing duration
                        start_time = time.time()
                        try:
                            with tracer.start_as_current_span(
                                "zmq_listener.process_message"
                            ):
                                await self.operator.process(msg)

                            # Record success
                            duration = time.time() - start_time
                            processing_duration_histogram.record(
                                duration, {"listener.type": "zmq", "status": "success"}
                            )
                            messages_processed_counter.add(1, {"listener.type": "zmq"})
                        except Exception as proc_error:
                            # Record failure
                            duration = time.time() - start_time
                            processing_duration_histogram.record(
                                duration, {"listener.type": "zmq", "status": "failed"}
                            )
                            messages_failed_counter.add(1, {"listener.type": "zmq"})
                            raise proc_error

                except zmq.Again:
                    # no message occured within the timeout period
                    pass
                except asyncio.exceptions.CancelledError:
                    # in case this is being done in a asyncio.create_task call
                    span.set_attribute("listener.cancelled", True)
                    span.set_attribute("listener.messages_processed", message_count)
                    if self._active:
                        _active_listeners_count -= 1
                        self._active = False
                    pass
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    logger.error(f"Error processing message: {e}")
                    if self._active:
                        _active_listeners_count -= 1
                        self._active = False
                    raise

    async def stop(self):
        with tracer.start_as_current_span("zmq_listener.stop"):
            self.stop_requested = True
            self.zmq_socket.close()
            self.zmq_socket.context.term()


def setup_pub_socket(zmq_endpoint: str) -> zmq.Socket:
    """Setup a ZMQ publisher socket.

    Parameters
    ----------
    zmq_endpoint : str
        ZMQ endpoint to connect to

    Returns
    -------
    zmq.Socket
        Configured ZMQ publisher socket
    """
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(zmq_endpoint)
    socket.subscribe("")
    logger.info(f"Connected to ZMQ endpoint: {zmq_endpoint}")
    return socket
