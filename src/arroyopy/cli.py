"""
CLI tool for running arroyo units from configuration files.

This tool provides a command-line interface to load and run
arroyo units defined in YAML configuration files.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import List, Optional

import typer

from arroyopy.config import (
    ConfigurationError,
    load_unit_from_yaml,
    load_units_from_yaml,
)
from arroyopy.unit import Unit

app = typer.Typer(
    help="Arroyo unit runner - Run stream processing pipelines from config files"
)

# Global list to track running units for graceful shutdown
running_units: List[Unit] = []


# ============================================================================
# Core Business Logic (easily testable without mocking)
# ============================================================================


async def run_units_async(units: List[Unit], logger: logging.Logger) -> None:
    """
    Run multiple units concurrently.

    Pure async function that can be tested directly.
    """
    tasks = []
    for unit in units:
        logger.info(f"Starting unit '{unit.name}'")
        task = asyncio.create_task(unit.start())
        tasks.append(task)

    # Wait for all units to complete
    await asyncio.gather(*tasks)


def validate_units_info(units: List[Unit], logger: logging.Logger) -> None:
    """
    Validate and log information about units.

    Pure function that can be tested directly.
    """
    logger.info("✓ Configuration is valid")
    logger.info(f"✓ Found {len(units)} unit(s):")

    for unit in units:
        logger.info(f"  - {unit.name}")
        logger.info(f"    Operator: {unit.operator.__class__.__name__}")
        logger.info(f"    Listeners: {len(unit.listeners)}")
        for listener in unit.listeners:
            logger.info(f"      - {listener.__class__.__name__}")
        logger.info(f"    Publishers: {len(unit.publishers)}")
        for publisher in unit.publishers:
            logger.info(f"      - {publisher.__class__.__name__}")


def format_unit_info(unit: Unit) -> dict:
    """
    Extract unit information as a dictionary.

    Pure function that can be tested directly.
    """
    info = {
        "name": unit.name,
        "operator": unit.operator.__class__.__name__,
        "listeners": len(unit.listeners),
        "publishers": len(unit.publishers),
    }
    if hasattr(unit, "description"):
        info["description"] = unit.description
    return info


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def shutdown_units(units: List[Unit]):
    """Gracefully shutdown all units."""
    logger = logging.getLogger(__name__)
    logger.info(f"Shutting down {len(units)} unit(s)...")

    for unit in units:
        try:
            await unit.stop()
        except Exception as e:
            logger.error(f"Error stopping unit '{unit.name}': {e}")

    logger.info("All units stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}")

    # Run async shutdown
    loop = asyncio.get_event_loop()
    if running_units:
        loop.create_task(shutdown_units(running_units))

    sys.exit(0)


@app.command()
def run(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
    unit_name: Optional[str] = typer.Option(
        None, "--unit", "-u", help="Specific unit to run (if config has multiple)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    Run an arroyo unit from a configuration file.

    Examples:

        # Run a single unit from config
        arroyo-run pipeline.yaml

        # Run a specific unit from multi-unit config
        arroyo-run config.yaml --unit data_processor

        # Run with verbose logging
        arroyo-run pipeline.yaml --verbose
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Check if config file exists
    if not Path(config_file).exists():
        logger.error(f"Configuration file not found: {config_file}")
        raise typer.Exit(code=1)

    # Add config file's directory to sys.path to allow importing local modules
    config_dir = str(Path(config_file).parent.resolve())
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    try:
        # Load unit(s)
        if unit_name:
            logger.info(f"Loading unit '{unit_name}' from {config_file}")
            unit = load_unit_from_yaml(config_file, unit_name)
            units = [unit]
        else:
            logger.info(f"Loading units from {config_file}")
            units = load_units_from_yaml(config_file)

        # Add to global list for signal handling
        running_units.extend(units)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run units using extracted business logic
        asyncio.run(run_units_async(units, logger))

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error running unit(s): {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def validate(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    Validate a configuration file without running it.

    This loads and instantiates all components to verify the configuration
    is correct, but doesn't actually start processing.

    Example:

        arroyo-run validate pipeline.yaml
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    if not Path(config_file).exists():
        logger.error(f"Configuration file not found: {config_file}")
        raise typer.Exit(code=1)

    # Add config file's directory to sys.path to allow importing local modules
    config_dir = str(Path(config_file).parent.resolve())
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    try:
        units = load_units_from_yaml(config_file)

        # Use extracted business logic
        validate_units_info(units, logger)

        typer.echo("\nConfiguration is valid! ✓")

    except ConfigurationError as e:
        logger.error(f"✗ Configuration error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"✗ Validation error: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def list_units(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
):
    """
    List all units defined in a configuration file.

    Example:

        arroyo-run list-units pipeline.yaml
    """
    logger = logging.getLogger(__name__)

    if not Path(config_file).exists():
        logger.error(f"Configuration file not found: {config_file}")
        raise typer.Exit(code=1)

    # Add config file's directory to sys.path to allow importing local modules
    config_dir = str(Path(config_file).parent.resolve())
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    try:
        units = load_units_from_yaml(config_file)

        typer.echo(f"\nUnits in {config_file}:\n")

        for i, unit in enumerate(units, 1):
            info = format_unit_info(unit)
            typer.echo(f"{i}. {info['name']}")
            if "description" in info:
                typer.echo(f"   Description: {info['description']}")
            typer.echo(f"   Operator: {info['operator']}")
            typer.echo(f"   Listeners: {info['listeners']}")
            typer.echo(f"   Publishers: {info['publishers']}")
            typer.echo()

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error reading configuration: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
