"""
Unit tests for the Unit class and configuration system.
"""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from arroyopy.config import (
    ConfigurationError,
    _import_class,
    _instantiate_component,
    load_unit_from_config,
    load_unit_from_yaml,
    load_units_from_yaml,
)
from arroyopy.listener import Listener
from arroyopy.operator import Operator
from arroyopy.publisher import Publisher
from arroyopy.schemas import Message
from arroyopy.unit import Unit


# Concrete operator for YAML/config loading tests
# Renamed to avoid pytest trying to collect it as a test class
class ConcreteOperator(Operator):
    """Simple concrete operator for testing."""

    async def process(self, message: Message) -> Message:
        return message


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
    """Test basic unit initialization."""
    unit = Unit(name="test_unit", operator=mock_operator)

    assert unit.name == "test_unit"
    assert unit.operator is mock_operator
    assert unit.listeners == []
    assert unit.publishers == []


@pytest.mark.asyncio
async def test_unit_with_components(mock_operator, mock_listener, mock_publisher):
    """Test unit initialization with listeners and publishers."""
    listener = mock_listener(mock_operator)

    # Create unit without components first to avoid event loop issues
    unit = Unit(name="test_unit", operator=mock_operator)

    # Add components using async methods
    await unit.add_listener(listener)
    unit.add_publisher(mock_publisher)

    assert len(unit.listeners) == 1
    assert len(unit.publishers) == 1


@pytest.mark.asyncio
async def test_add_listener(mock_operator, mock_listener):
    """Test adding a listener to a unit."""
    unit = Unit(name="test_unit", operator=mock_operator)
    listener = mock_listener(mock_operator)

    await unit.add_listener(listener)

    assert len(unit.listeners) == 1


def test_add_publisher(mock_operator, mock_publisher):
    """Test adding a publisher to a unit."""
    unit = Unit(name="test_unit", operator=mock_operator)

    unit.add_publisher(mock_publisher)

    assert len(unit.publishers) == 1


def test_unit_repr(mock_operator):
    """Test unit string representation."""
    unit = Unit(name="test_unit", operator=mock_operator)

    repr_str = repr(unit)
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
    config = {"class": "_test.test_unit.ConcreteOperator", "kwargs": {}}

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


def test_load_unit_from_config_minimal():
    """Test loading a minimal unit configuration."""
    config = {
        "name": "test_unit",
        "operator": {"class": "_test.test_unit.ConcreteOperator"},
    }

    unit = load_unit_from_config(config)
    assert unit.name == "test_unit"
    assert isinstance(unit.operator, ConcreteOperator)
    assert len(unit.listeners) == 0
    assert len(unit.publishers) == 0


def test_load_unit_missing_name():
    """Test loading unit with missing name."""
    config = {"operator": {"class": "_test.test_unit.ConcreteOperator"}}

    with pytest.raises(ConfigurationError, match="must have a 'name' field"):
        load_unit_from_config(config)


def test_load_unit_missing_operator():
    """Test loading unit with missing operator."""
    config = {"name": "test_unit"}

    with pytest.raises(ConfigurationError, match="must have an 'operator' field"):
        load_unit_from_config(config)


# ============================================================================
# YAML loading tests
# ============================================================================


def test_load_single_unit_from_yaml():
    """Test loading a single unit from YAML file."""
    yaml_content = """
name: test_unit
operator:
  class: _test.test_unit.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        units = load_units_from_yaml(yaml_path)
        assert len(units) == 1
        assert units[0].name == "test_unit"
        assert isinstance(units[0].operator, ConcreteOperator)
    finally:
        Path(yaml_path).unlink()


def test_load_multiple_units_from_yaml():
    """Test loading multiple units from YAML file."""
    yaml_content = """
units:
  - name: unit1
    operator:
      class: _test.test_unit.ConcreteOperator
  - name: unit2
    operator:
      class: _test.test_unit.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        units = load_units_from_yaml(yaml_path)
        assert len(units) == 2
        assert units[0].name == "unit1"
        assert units[1].name == "unit2"
    finally:
        Path(yaml_path).unlink()


def test_load_unit_by_name():
    """Test loading a specific unit by name."""
    yaml_content = """
units:
  - name: unit1
    operator:
      class: _test.test_unit.ConcreteOperator
  - name: unit2
    operator:
      class: _test.test_unit.ConcreteOperator
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name

    try:
        unit = load_unit_from_yaml(yaml_path, "unit2")
        assert unit.name == "unit2"
    finally:
        Path(yaml_path).unlink()


def test_load_nonexistent_file():
    """Test loading from nonexistent file."""
    with pytest.raises(ConfigurationError, match="not found"):
        load_units_from_yaml("/nonexistent/path.yaml")


def test_load_empty_yaml():
    """Test loading empty YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="empty"):
            load_units_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()


def test_load_invalid_yaml():
    """Test loading invalid YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content:")
        yaml_path = f.name

    try:
        with pytest.raises(ConfigurationError, match="parse"):
            load_units_from_yaml(yaml_path)
    finally:
        Path(yaml_path).unlink()
