import logging
import signal
from typing import Callable
from uuid import uuid4

import numpy as np
import zmq

# Maintain a map of LabView datatypes. LabView sends BigE,
# and Numpy assumes LittleE, so adjust that too.
# LabView also has an 'Extended Float' and I don't know how to map that.
DATATYPE_MAP = {
    "U8": np.dtype(np.uint8).newbyteorder(">"),
    "U16": np.dtype(np.uint16).newbyteorder(">"),
    "U32": np.dtype(np.uint32).newbyteorder(">"),
    "U64": np.dtype(np.uint64).newbyteorder(">"),
    "I8": np.dtype(np.int8).newbyteorder(">"),
    "I16": np.dtype(np.int16).newbyteorder(">"),
    "I32": np.dtype(np.int32).newbyteorder(">"),
    "I64": np.dtype(np.int64).newbyteorder(">"),
    "Single Float": np.dtype(np.single).newbyteorder(">"),
    "Double Float": np.dtype(np.double).newbyteorder(">"),
}

logger = logging.getLogger(__name__)

received_sigterm = {"received": False}  # Define the variable received_sigterm


def handle_sigterm(signum, frame):
    logger.info("SIGTERM received, stopping...")
    received_sigterm["received"] = True


# Register the handler for SIGTERM
signal.signal(signal.SIGTERM, handle_sigterm)


class ZMQImageListener:
    def __init__(
        self,
        start_function: Callable[[dict], None],
        event_function: Callable[[int, np.ndarray], None],
        stop_function: Callable[[dict], None],
        zmq_pub_address: str = "tcp://127.0.0.1",
        zmq_pub_port: int = 5555,
    ):
        self.zmq_pub_address = zmq_pub_address
        self.zmq_pub_port = zmq_pub_port
        self.start_function = start_function
        self.stop_function = stop_function
        self.event_function = event_function
        self.stop = False

    def start(self):
        ctx = zmq.Context()
        socket = ctx.socket(zmq.SUB)
        logger.info(f"binding to: {self.zmq_pub_address}:{self.zmq_pub_port}")
        socket.connect(f"{self.zmq_pub_address}:{self.zmq_pub_port}")
        socket.setsockopt(zmq.SUBSCRIBE, b"")

        while True:
            try:
                if self.stop or received_sigterm["received"]:
                    logger.info("Stopping listener.")
                    break

                message = socket.recv_json()
                logger.info(f"{message=}")
                message_type = message["msg_type"]
                if message_type == "start":
                    message["scan_name"] = f"temporary scan name{uuid4()}"  # temporary
                    self.start_function(message)
                    if logger.getEffectiveLevel() == logging.DEBUG:
                        logger.debug(f"start: {message}")
                    continue
                if message_type == "metadata":
                    self.stop_function(message)

                    continue
                if message_type != "image":
                    logger.error(f"Received unexpected message: {message}")
                    continue
                # Must be an event with an image
                image_info = message
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug(f"event: {image_info}")

                # Image should be the next thing received
                buffer = socket.recv()
                shape = (image_info["Width"], image_info["Height"])
                frame_number = image_info["Frame Number"]
                dtype = DATATYPE_MAP.get(image_info["data_type"])
                if not dtype:
                    logger.error(f"Received unexpected data type: {image_info}")
                    continue
                array_received = np.frombuffer(buffer, dtype=dtype).reshape(shape)
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug(
                        f"received: {frame_number=} {shape=} {dtype=} {array_received}"
                    )
                if self.event_function:
                    self.event_function(image_info, array_received)

            except Exception as e:
                logger.error(e)
                if message:
                    logger.exception(f"Error dealing with {message=}")

    def stop(self):
        self.stop = True
