import logging
from typing import List
from uuid import uuid4

import numpy as np

from als_arroyo.message import AbstractMessageParser

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


class LabviewXPSParser(AbstractMessageParser):

    async def parse(self, message: List[bytes]):
        try:

            logger.info(f"{message=}")
            message_type = message["msg_type"]
            if message_type == "start":
                message["scan_name"] = f"temporary scan name{uuid4()}"  # temporary
                self.start_function(message)
                if logger.getEffectiveLevel() == logging.DEBUG:
                    logger.debug(f"start: {message}")
                return
            if message_type == "metadata":
                self.stop_function(message)

                return
            if message_type != "image":
                logger.error(f"Received unexpected message: {message}")
                return
            # Must be an event with an image
            image_info = message
            if logger.getEffectiveLevel() == logging.DEBUG:
                logger.debug(f"event: {image_info}")

            # Image should be the next thing received
            buffer = socket.recv()]
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