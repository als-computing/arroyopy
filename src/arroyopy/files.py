import logging
from pathlib import Path

from pydantic import BaseModel
from watchfiles import awatch

from arroyopy import Listener, Operator
from arroyopy.schemas import Message

logger = logging.getLogger("data_watcher")
logger.setLevel("INFO")
logger.addHandler(logging.StreamHandler())


class FileWatcherMessage(Message, BaseModel):
    file_path: str
    is_directory: bool


class FileWatcherListener(Listener):
    def __init__(self, directory: str, operator: Operator):
        self.directory = directory
        self.operator = operator

    async def start(self):
        logger.info(f"🔍 Watching directory recursively: {self.directory}")
        async for changes in awatch(self.directory):
            for change_type, path_str in changes:
                path = Path(path_str)
                logger.debug(f"📦 Detected: {change_type} on {path}")
                message = FileWatcherMessage(
                    file_path=str(path), is_directory=path.is_dir()
                )
                await self.operator.process(message)

    async def stop(self):
        pass
