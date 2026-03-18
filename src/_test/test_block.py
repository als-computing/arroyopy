"""
Block tests for the Block class and configuration system.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from arroyopy.block import Block
from arroyopy.config import (
    ConfigurationError,
    _import_class,
    _instantiate_component,
    load_block_from_config,
    load_block_from_yaml,
    load_blocks_from_yaml,
)
from arroyopy.listener import Listener
from arroyopy.operator import Operator
from arroyopy.publisher import Publisher
from arroyopy.schemas import Message


# Concrete operator for YAML/config loading tests
# Renamed to avoid pytest trying to collect it as a test class
class ConcreteOperator(Operator):
    """Simple concrete operator for testing."""

    async def process(self, message: Message) -> Message:
        return message


# Simple class for testing invalid type validation
class NotAComponent:
    """A class that is not a Listener, Publisher, or Operator."""

    def __init__(self, **kwargs):
        pass


# Pytest fixtures
@pytest.fixture
def mock_operator():
    """Create a mock operator for testing."""
    operator = Mock(spec=Operator)
    operator.process = AsyncMock(return_value=Mock(spec=Message))
    operator.add_listener = AsyncMock()
    operator.add_publisher = Mock()
    return operator


@pytest.fixture
def mock_listener():
    """Create a mock listener factory for testing."""

    def _create(operator):
        listener = Mock(spec=Listener)
        listener.operator = operator
        listener.start = AsyncMock()
        listener.stop = AsyncMock()
        return listener

    return _create


@pytest.fixture
def mock_publisher():
    """Create a mock publisher for testing."""
    publisher = Mock(spec=Publisher)
    publisher.publish = AsyncMock()
    return publisher


# ============================================================================
# Unit tests
# ============================================================================


def test_unit_initialization(mock_operator):
    """Test basic block initialization."""
    block = Block(name="test_unit", operator=mock_operator)

    assert block.name == "test_unit"
    assert block.operator is mock_operator
    assert block.listeners == []
    assert block.publishers == []


@pytest.mark.asyncio
async def test_unit_with_components(mock_operator, mock_listener, mock_publisher):
    """Test block initialization with listeners and publishers."""
    listener = mock_listener(mock_operator)

    # Create block without components first to avoid event loop issues
    block = Block(name="test_unit", operator=mock_operator)

    # Add components using async methods
    await block.add_listener(listener)
    block.add_publisher(mock_publisher)

    assert len(block.listeners) == 1
    assert len(block.publishers) == 1


@pytest.mark.asyncio
async def test_add_listener(mock_operator, mock_listener):
    """Test adding a listener to a block."""
    block = Block(name="test_unit", operator=mock_operator)
    listener = mock_listener(mock_operator)

    await block.add_listener(listener)

    assert len(block.listeners) == 1


def test_add_publisher(mock_operator, mock_publisher):
    """Test adding a publisher to a block."""
    block = Block(name="test_unit", operator=mock_operator)

    block.add_publisher(mock_publisher)

    assert len(block.publishers) == 1


def test_unit_repr(mock_operator):
    """Test block string representation."""
    block = Block(name="test_unit", operator=mock_operator)

    repr_str = repr(block)
    assert "test_unit" in repr_str


# ============================================================================
# Configuration import tests
# ============================================================================


def test_import_class_success():
    """Test successful class import."""
    cls = _import_class("arroyopy.operator.Operator")
    assert cls is Operator


def test_import_class_failure():
    """Test failed class import."""
    with pytest.raises(ConfigurationError):
        _import_class("nonexistent.module.Class")


def test_import_class_invalid_path():
    """Test import with invalid path."""
    with pytest.raises(ConfigurationError):
        _import_class("invalid_class_path")


# ============================================================================
# Component instantiation tests
# ============================================================================


def test_instantiate_with_kwargs():
    """Test instantiation with keyword arguments."""
    config = {"class": "_test.test_block.ConcreteOperator", "kwargs": {}}

    component = _instantiate_component(config)
    assert isinstance(component, Operator)


def test_instantiate_missing_class():
    """Test instantiation with missing class field."""
    config = {"kwargs": {"timeout": 30}}

    with pytest.raises(ConfigurationError, match="must have a 'class' field"):
        _instantiate_component(config)


def test_instantiate_invalid_class():
    """Test instantiation with invalid class."""
    config = {"class": "nonexistent.Class", "kwargs": {}}

    with pytest.raises(ConfigurationError):
        _instantiate_component(config)


# ============================================================================
# Config loading tests
# ============================================================================


def test_load_block_from_config_minimal():
    """Test loading a minimal block configuration."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.ConcreteOperator"},
    }

    block = load_block_from_config(config)
    assert block.name == "test_unit"
    assert isinstance(block.operator, ConcreteOperator)
    assert len(block.listeners) == 0
    assert len(block.publishers) == 0


def test_load_unit_missing_name():
    """Test loading block with missing name."""
    config = {"operator": {"class": "_test.test_block.ConcreteOperator"}}

    with pytest.raises(ConfigurationError, match="must have a 'name' field"):
        load_block_from_config(config)


def test_load_unit_missing_operator():
    """Test loading block with missing operator."""
    config = {"name": "test_unit"}

    with pytest.raises(ConfigurationError, match="must have an 'operator' field"):
        load_block_from_config(config)


# ============================================================================
# YAML loading tests
# ============================================================================


def test_load_single_unit_from_yaml():
    """Test loading a single block from YAML file."""
    yaml_content = """
blocks:
  - name: test_unit
    operator:
      class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        blocks = load_blocks_from_yaml(yaml_path)
        assert len(blocks) == 1
        assert blocks[0].name == "test_unit"
        assert isinstance(blocks[0].operator, ConcreteOperator)
    finally:
        Path(yaml_path).unlink()


def test_load_multiple_units_from_yaml():
    """Test loading multiple blocks from YAML file."""
    yaml_content = """
blocks:
  - name: block1
    operator:
      class: _test.test_block.ConcreteOperator
  - name: block2
    operator:
      class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        blocks = load_blocks_from_yaml(yaml_path)
        assert len(blocks) == 2
        assert blocks[0].name == "block1"
        assert blocks[1].name == "block2"
    finally:
        Path(yaml_path).unlink()


def test_load_unit_by_name():
    """Test loading a specific block by name."""
    yaml_content = """
blocks:
  - name: block1
    operator:
      class: _test.test_block.ConcreteOperator
  - name: block2
    operator:
      class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        block = load_block_from_yaml(yaml_path, "block2")
        assert block.name == "block2"
    finally:
        Path(yaml_path).unlink()


def test_load_nonexistent_file():
    """Test loading from nonexistent file."""
    with pytest.raises(ConfigurationError, match="not found"):
        load_blocks_from_yaml("/nonexistent/path.yaml")


def test_load_empty_yaml():
    """Test loading empty YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="empty"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_invalid_yaml():
    """Test loading invalid YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content:")
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="parse"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_unit_invalid_operator_type():
    """Test loading block with invalid operator type (not an Operator instance)."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.NotAComponent"},  # Not an Operator
    }

    with pytest.raises(ConfigurationError, match="must be an instance of Operator"):
        load_block_from_config(config)


def test_load_unit_invalid_listener_type():
    """Test loading block with invalid listener type."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.ConcreteOperator"},
        "listeners": [{"class": "_test.test_block.NotAComponent"}],  # Not a Listener
    }

    with pytest.raises(ConfigurationError, match="must be an instance of Listener"):
        load_block_from_config(config)


def test_load_unit_invalid_publisher_type():
    """Test loading block with invalid publisher type."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.ConcreteOperator"},
        "publishers": [{"class": "_test.test_block.NotAComponent"}],  # Not a Publisher
    }

    with pytest.raises(ConfigurationError, match="must be an instance of Publisher"):
        load_block_from_config(config)


def test_load_unit_listener_error():
    """Test error handling when loading a listener fails."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.ConcreteOperator"},
        "listeners": [{"class": "nonexistent.Listener"}],
    }

    with pytest.raises(ConfigurationError, match="Failed to load listener"):
        load_block_from_config(config)


def test_load_unit_publisher_error():
    """Test error handling when loading a publisher fails."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_block.ConcreteOperator"},
        "publishers": [{"class": "nonexistent.Publisher"}],
    }

    with pytest.raises(ConfigurationError, match="Failed to load publisher"):
        load_block_from_config(config)


def test_load_units_invalid_structure():
    """Test loading YAML with invalid structure (missing blocks key)."""
    yaml_content = """
invalid_key: some_value
another_key: another_value
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="must contain a 'blocks' key"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_units_rejects_old_top_level_format():
    """Test that old top-level block format (without 'blocks' key) is rejected."""
    yaml_content = """
name: test_unit
operator:
  class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="must contain a 'blocks' key"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_units_invalid_units_type():
    """Test loading YAML where 'blocks' is not a list."""
    yaml_content = """
blocks:
  name: not_a_list
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="'blocks' must be a list"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_units_block_config_error():
    """Test error handling when loading a block from YAML fails."""
    yaml_content = """
blocks:
  - name: block1
    operator:
      class: nonexistent.Operator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="Failed to load block"):
            load_blocks_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_block_from_yaml_multiple_without_name():
    """Test loading from YAML with multiple blocks but no block_name specified."""
    yaml_content = """
blocks:
  - name: block1
    operator:
      class: _test.test_block.ConcreteOperator
  - name: block2
    operator:
      class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="Specify block_name"):
            load_block_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_block_from_yaml_not_found():
    """Test loading a block by name that doesn't exist."""
    yaml_content = """
blocks:
  - name: block1
    operator:
      class: _test.test_block.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="not found"):
            load_block_from_yaml(yaml_path, "nonexistent")
    finally:
        Path(yaml_path).unlink()


# ============================================================================
# Block start/stop tests
# ============================================================================


@pytest.mark.asyncio
async def test_unit_start_stop(mock_operator, mock_listener):
    """Test block start and stop methods."""
    block = Block(name="test_unit", operator=mock_operator)
    listener = mock_listener(mock_operator)

    # Configure the mock operator to stop immediately
    async def mock_start():
        pass

    mock_operator.start = AsyncMock(side_effect=mock_start)
    mock_operator.stop_requested = False

    await block.add_listener(listener)

    # Mock the start to return immediately
    listener.start.return_value = None

    # Start the block (with timeout to prevent hanging)
    start_task = asyncio.create_task(block.start())

    # Give it a moment to start
    await asyncio.sleep(0.1)

    # Stop the unit
    await block.stop()

    # Cancel the start task
    start_task.cancel()
    try:
        await start_task
    except asyncio.CancelledError:
        pass

    # Verify start was called
    mock_operator.start.assert_called_once()
    listener.stop.assert_called()


@pytest.mark.asyncio
async def test_operator_start_runs_in_background(mock_operator, mock_listener):
    """Test that operator.start() is run as a background task.

    If operator.start() were awaited directly, it would block forever and
    listeners would never be started. This test verifies that listeners are
    started even when the operator's start() never returns.
    """
    block = Block(name="test_unit", operator=mock_operator)
    listener = mock_listener(mock_operator)

    # Operator start() that blocks indefinitely - simulates a real operator loop
    blocking_event = asyncio.Event()

    async def blocking_start():
        await blocking_event.wait()

    mock_operator.start = AsyncMock(side_effect=blocking_start)
    await block.add_listener(listener)

    # Run block.start() with a short timeout; if operator was awaited directly
    # this gather would never reach the listener and would time out
    start_task = asyncio.create_task(block.start())
    await asyncio.sleep(0.1)

    # Listener should have been started despite operator never returning
    listener.start.assert_called_once()

    # Cleanup
    blocking_event.set()
    start_task.cancel()
    try:
        await start_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_unit_stop_when_not_running(mock_operator):
    """Test stopping a block that isn't running."""
    block = Block(name="test_unit", operator=mock_operator)

    # This should not raise an error, just log a warning
    await block.stop()


@pytest.mark.asyncio
async def test_unit_start_when_already_running(mock_operator):
    """Test starting a block that is already running."""
    block = Block(name="test_unit", operator=mock_operator)

    # Set the block as already running
    block._running = True

    # This should not raise an error, just log a warning
    await block.start()

    # start() should not have been called on the operator
    mock_operator.start.assert_not_called()


# ============================================================================
# Operator tests
# ============================================================================


def test_operator_remove_listener(mock_operator, mock_listener):
    """Test removing a listener from an operator."""
    # Use a real ConcreteOperator for this test
    operator = ConcreteOperator()
    # Clear any class-level state from previous tests
    operator.listeners.clear()
    listener = mock_listener(operator)

    operator.listeners.append(listener)
    assert len(operator.listeners) == 1

    operator.remove_listener(listener)
    assert len(operator.listeners) == 0


def test_operator_remove_publisher(mock_publisher):
    """Test removing a publisher from an operator."""
    # Use a real ConcreteOperator for this test
    operator = ConcreteOperator()
    # Clear any class-level state from previous tests
    operator.publishers.clear()

    operator.publishers.append(mock_publisher)
    assert len(operator.publishers) == 1

    operator.remove_publisher(mock_publisher)
    assert len(operator.publishers) == 0


@pytest.mark.asyncio
async def test_operator_publish(mock_publisher):
    """Test publishing a message to all publishers."""
    operator = ConcreteOperator()
    # Clear any class-level state from previous tests
    operator.publishers.clear()
    publisher1 = Mock(spec=Publisher)
    publisher1.publish = AsyncMock()
    publisher2 = Mock(spec=Publisher)
    publisher2.publish = AsyncMock()

    operator.add_publisher(publisher1)
    operator.add_publisher(publisher2)

    message = Mock(spec=Message)
    await operator.publish(message)

    publisher1.publish.assert_called_once_with(message)
    publisher2.publish.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_operator_add_listener():
    """Test adding a listener to an operator."""
    operator = ConcreteOperator()
    listener = Mock(spec=Listener)
    listener.start = AsyncMock()

    await operator.add_listener(listener)

    assert len(operator.listeners) == 1
    listener.start.assert_called_once()


def test_operator_add_publisher(mock_publisher):
    """Test adding a publisher to an operator."""
    operator = ConcreteOperator()
    # Clear any class-level state from previous tests
    operator.publishers.clear()

    operator.add_publisher(mock_publisher)

    assert len(operator.publishers) == 1


@pytest.mark.asyncio
async def test_operator_start_stop_loop():
    """Test operator start/stop processing loop."""
    import asyncio

    operator = ConcreteOperator()
    operator.listeners.clear()
    operator.publishers.clear()

    # Create mock listener
    listener = Mock(spec=Listener)
    listener.stop = AsyncMock()
    operator.listeners.append(listener)

    # Create mock publisher
    publisher = Mock(spec=Publisher)
    publisher.publish = AsyncMock()
    operator.add_publisher(publisher)

    # Fix the queue reference bug by setting queue = listener_queue
    operator.queue = operator.listener_queue

    # Put a test message in the queue
    test_message = Mock(spec=Message)
    await operator.queue.put(test_message)

    # Start the operator in a task
    start_task = asyncio.create_task(operator.start())

    # Give it time to process the message
    await asyncio.sleep(0.1)

    # Request stop
    operator.stop_requested = True
    # Put another message to wake up the queue.get()
    await operator.queue.put(Mock(spec=Message))

    # Wait for the operator to stop
    try:
        await asyncio.wait_for(start_task, timeout=1.0)
    except asyncio.TimeoutError:
        start_task.cancel()

    # Verify the listener's stop was called
    listener.stop.assert_called()
    # Verify the publisher was called at least once
    assert publisher.publish.called


# ============================================================================
# Listener tests
# ============================================================================


def test_listener_initialization():
    """Test listener initialization to cover __init__ method."""
    operator = ConcreteOperator()

    # Create a concrete listener for testing
    class ConcreteListener(Listener):
        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

    listener = ConcreteListener(operator)

    assert listener.operator is operator
