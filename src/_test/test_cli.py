"""Tests for CLI commands."""
import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from arroyopy.cli import (
    app,
    format_unit_info,
    run_units_async,
    setup_logging,
    shutdown_units,
    validate_units_info,
)
from arroyopy.config import ConfigurationError
from arroyopy.unit import Unit

runner = CliRunner()


@pytest.fixture
def mock_unit():
    """Create a mock Unit instance."""
    unit = Mock(spec=Unit)
    unit.name = "test_unit"
    unit.start = AsyncMock()
    unit.stop = AsyncMock()
    unit.operator = Mock()
    unit.operator.__class__.__name__ = "TestOperator"
    unit.listeners = [Mock()]
    unit.listeners[0].__class__.__name__ = "TestListener"
    unit.publishers = [Mock()]
    unit.publishers[0].__class__.__name__ = "TestPublisher"
    return unit


@pytest.fixture
def mock_units(mock_unit):
    """Create a list of mock units."""
    unit2 = Mock(spec=Unit)
    unit2.name = "test_unit_2"
    unit2.start = AsyncMock()
    unit2.stop = AsyncMock()
    unit2.operator = Mock()
    unit2.operator.__class__.__name__ = "AnotherOperator"
    unit2.listeners = []
    unit2.publishers = []
    return [mock_unit, unit2]


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("test: config")
    return str(config_file)


@pytest.fixture
def mock_load_units(mock_unit):
    """Fixture to patch load_units_from_yaml."""
    with patch("arroyopy.cli.load_units_from_yaml", return_value=[mock_unit]) as mock:
        yield mock


@pytest.fixture
def mock_load_unit(mock_unit):
    """Fixture to patch load_unit_from_yaml."""
    with patch("arroyopy.cli.load_unit_from_yaml", return_value=mock_unit) as mock:
        yield mock


@pytest.fixture
def mock_signal():
    """Fixture to patch signal.signal."""
    with patch("arroyopy.cli.signal.signal") as mock:
        yield mock


@pytest.fixture
def mock_validate_logic():
    """Fixture to patch validate_units_info."""
    with patch("arroyopy.cli.validate_units_info") as mock:
        yield mock


@pytest.fixture
def mock_run_logic():
    """Fixture to patch run_units_async."""
    with patch("arroyopy.cli.run_units_async", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_asyncio_run():
    """Fixture to patch asyncio.run."""
    with patch(
        "asyncio.run",
        side_effect=lambda coro: asyncio.get_event_loop().run_until_complete(coro),
    ) as mock:
        yield mock


@pytest.fixture
def mock_format_logic():
    """Fixture to wrap format_unit_info for spying."""
    with patch("arroyopy.cli.format_unit_info", wraps=format_unit_info) as mock:
        yield mock


@pytest.fixture
def mock_logging_config():
    """Fixture to patch logging.basicConfig."""
    with patch("logging.basicConfig") as mock:
        yield mock


# ============================================================================
# Tests for Business Logic (no mocking needed!)
# ============================================================================


class TestBusinessLogic:
    """Test core business logic functions without CLI framework."""

    @pytest.mark.asyncio
    async def test_run_units_async(self, mock_units, caplog):
        """Test running units concurrently."""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            await run_units_async(mock_units, logger)

        # Verify all units were started
        for unit in mock_units:
            unit.start.assert_called_once()
            assert f"Starting unit '{unit.name}'" in caplog.text

    def test_validate_units_info(self, mock_units, caplog):
        """Test validation info logging."""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            validate_units_info(mock_units, logger)

        # Verify validation messages
        assert "Configuration is valid" in caplog.text
        assert "Found 2 unit(s)" in caplog.text
        assert "test_unit" in caplog.text
        assert "test_unit_2" in caplog.text
        assert "TestOperator" in caplog.text
        assert "AnotherOperator" in caplog.text

    def test_format_unit_info(self, mock_unit):
        """Test unit info formatting."""
        info = format_unit_info(mock_unit)

        assert info["name"] == "test_unit"
        assert info["operator"] == "TestOperator"
        assert info["listeners"] == 1
        assert info["publishers"] == 1

    def test_format_unit_info_with_description(self, mock_unit):
        """Test unit info formatting with description."""
        mock_unit.description = "A test unit"

        info = format_unit_info(mock_unit)

        assert info["description"] == "A test unit"


# ============================================================================
# Tests for Infrastructure (signal handling, logging, shutdown)
# ============================================================================


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_info_level(self, mock_logging_config):
        """Test that logging is set up with INFO level by default."""
        setup_logging(verbose=False)
        mock_logging_config.assert_called_once()
        assert mock_logging_config.call_args[1]["level"] == logging.INFO

    def test_setup_logging_debug_level(self, mock_logging_config):
        """Test that logging is set up with DEBUG level when verbose."""
        setup_logging(verbose=True)
        mock_logging_config.assert_called_once()
        assert mock_logging_config.call_args[1]["level"] == logging.DEBUG


class TestShutdownUnits:
    """Test shutdown_units function."""

    @pytest.mark.asyncio
    async def test_shutdown_units_success(self, mock_units, caplog):
        """Test successful shutdown of all units."""
        with caplog.at_level(logging.INFO):
            await shutdown_units(mock_units)

        # Verify all units were stopped
        for unit in mock_units:
            unit.stop.assert_called_once()

        # Verify logging
        assert "Shutting down 2 unit(s)" in caplog.text
        assert "All units stopped" in caplog.text

    @pytest.mark.asyncio
    async def test_shutdown_units_with_error(self, mock_units, caplog):
        """Test shutdown when a unit raises an error."""
        # Make first unit raise an error on stop
        mock_units[0].stop.side_effect = Exception("Stop failed")

        with caplog.at_level(logging.ERROR):
            await shutdown_units(mock_units)

        # Verify error was logged
        assert "Error stopping unit 'test_unit'" in caplog.text
        assert "Stop failed" in caplog.text

        # Verify second unit was still stopped
        mock_units[1].stop.assert_called_once()


# ============================================================================
# Tests for CLI Commands (minimal mocking, just verify integration)
# ============================================================================


class TestRunCommand:
    """Test the 'run' command."""

    def test_run_file_not_found(self, caplog):
        """Test run command with non-existent file."""
        with caplog.at_level(logging.ERROR):
            result = runner.invoke(app, ["run", "nonexistent.yaml"])
        assert result.exit_code == 1
        assert "Configuration file not found" in caplog.text

    def test_run_configuration_error(self, temp_config_file, caplog):
        """Test run command with configuration error."""
        with patch(
            "arroyopy.cli.load_units_from_yaml",
            side_effect=ConfigurationError("Invalid config"),
        ):
            with caplog.at_level(logging.ERROR):
                result = runner.invoke(app, ["run", temp_config_file])

            assert result.exit_code == 1
            assert "Configuration error" in caplog.text

    def test_run_calls_business_logic(
        self,
        temp_config_file,
        mock_load_units,
        mock_signal,
        mock_run_logic,
        mock_asyncio_run,
    ):
        """Test that run command calls the extracted business logic."""
        result = runner.invoke(app, ["run", temp_config_file])

        # Verify business logic was called
        mock_run_logic.assert_called_once()
        assert result.exit_code == 0


class TestValidateCommand:
    """Test the 'validate' command."""

    def test_validate_file_not_found(self):
        """Test validate command with non-existent file."""
        result = runner.invoke(app, ["validate", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_validate_calls_business_logic(
        self, temp_config_file, mock_unit, mock_load_units, mock_validate_logic
    ):
        """Test that validate command calls the extracted business logic."""
        result = runner.invoke(app, ["validate", temp_config_file])

        # Verify business logic was called with correct parameters
        mock_validate_logic.assert_called_once()
        args = mock_validate_logic.call_args[0]
        assert args[0] == [mock_unit]  # units
        # args[1] is the logger
        assert result.exit_code == 0

    def test_validate_configuration_error(self, temp_config_file, caplog):
        """Test validate with configuration error."""
        with patch(
            "arroyopy.cli.load_units_from_yaml",
            side_effect=ConfigurationError("Bad config"),
        ):
            with caplog.at_level(logging.ERROR):
                result = runner.invoke(app, ["validate", temp_config_file])

            assert result.exit_code == 1
            assert "Configuration error" in caplog.text


class TestListUnitsCommand:
    """Test the 'list-units' command."""

    def test_list_units_file_not_found(self):
        """Test list-units command with non-existent file."""
        result = runner.invoke(app, ["list-units", "nonexistent.yaml"])
        assert result.exit_code == 1

    def test_list_units_calls_format_logic(
        self, temp_config_file, mock_unit, mock_load_units, mock_format_logic
    ):
        """Test that list-units uses the format_unit_info function."""
        result = runner.invoke(app, ["list-units", temp_config_file])

        # Verify format function was called
        mock_format_logic.assert_called_once_with(mock_unit)
        assert result.exit_code == 0
        assert "test_unit" in result.stdout

    def test_list_units_configuration_error(self, temp_config_file, caplog):
        """Test list-units with configuration error."""
        with patch(
            "arroyopy.cli.load_units_from_yaml",
            side_effect=ConfigurationError("Bad config"),
        ):
            with caplog.at_level(logging.ERROR):
                result = runner.invoke(app, ["list-units", temp_config_file])

            assert result.exit_code == 1
            assert "Configuration error" in caplog.text
