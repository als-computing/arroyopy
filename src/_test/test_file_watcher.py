import asyncio
from pathlib import Path

import pytest

from arroyopy import Operator, Publisher
from arroyopy.files import FileWatcherListener


class MockPublisher(Publisher):
    def __init__(self):
        self.messages = []

    async def publish(self, message):
        self.messages.append(message)


class MockOperator(Operator):
    def __init__(self, publisher: MockPublisher):
        self.publisher = publisher

    async def process(self, message):
        await self.publisher.publish(message)


@pytest.mark.asyncio
async def test_filewatcher_detects_file_in_subdirectory(tmp_path: Path):
    # Set up directory and mocks
    publisher = MockPublisher()
    operator = MockOperator(publisher)
    listener = FileWatcherListener(str(tmp_path), operator)

    # Run the listener in the background
    task = asyncio.create_task(listener.start())

    # Give watchgod a moment to initialize
    await asyncio.sleep(0.5)

    # Create subdirectory and a valid .gb file in it
    subdir = tmp_path / "nested"
    subdir.mkdir()
    await asyncio.sleep(0.2)  # Allow watcher to pick up subdir creation

    gb_file = subdir / "test_file.gb"
    gb_file.write_text("mock content")

    # Allow time for the event to be picked up
    await asyncio.sleep(1.5)

    # Cancel the watcher task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Validate publisher received the notification
    assert len(publisher.messages) == 2
    assert Path(publisher.messages[0].file_path) == subdir
    assert publisher.messages[0].is_directory is True
    assert Path(publisher.messages[1].file_path) == gb_file
    assert publisher.messages[1].is_directory is False
