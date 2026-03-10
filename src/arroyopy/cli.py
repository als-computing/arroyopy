"""
CLI tool for running arroyo blocks from configuration files.

This tool provides a command-line interface to load and run
arroyo blocks defined in YAML configuration files.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import List, Optional

import typer

from arroyopy.block import Block
from arroyopy.config import (
    ConfigurationError,
    load_block_from_yaml,
    load_blocks_from_yaml,
)

app = typer.Typer(
    help="Arroyo block runner - Run stream processing pipelines from config files"
)

# Global list to track running blocks for graceful shutdown
running_blocks: List[Block] = []


# ============================================================================
# Core Business Logic (easily testable without mocking)
# ============================================================================


async def run_units_async(blocks: List[Block], logger: logging.Logger) -> None:
    """
    Run multiple blocks concurrently.

    Pure async function that can be tested directly.
    """
    tasks = []
    for block in blocks:
        logger.info(f"Starting block '{block.name}'")
        task = asyncio.create_task(block.start())
        tasks.append(task)

    # Wait for all blocks to complete
    await asyncio.gather(*tasks)


def validate_units_info(blocks: List[Block], logger: logging.Logger) -> None:
    """
    Validate and log information about blocks.

    Pure function that can be tested directly.
    """
    logger.info("✓ Configuration is valid")
    logger.info(f"✓ Found {len(blocks)} unit(s):")

    for block in blocks:
        logger.info(f"  - {block.name}")
        logger.info(f"    Operator: {block.operator.__class__.__name__}")
        logger.info(f"    Listeners: {len(block.listeners)}")
        for listener in block.listeners:
            logger.info(f"      - {listener.__class__.__name__}")
        logger.info(f"    Publishers: {len(block.publishers)}")
        for publisher in block.publishers:
            logger.info(f"      - {publisher.__class__.__name__}")


def format_block_info(block: Block) -> dict:
    """
    Extract block information as a dictionary.

    Pure function that can be tested directly.
    """
    info = {
        "name": block.name,
        "operator": block.operator.__class__.__name__,
        "listeners": len(block.listeners),
        "publishers": len(block.publishers),
    }
    if hasattr(block, "description"):
        info["description"] = block.description
    return info


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def shutdown_units(blocks: List[Block]):
    """Gracefully shutdown all blocks."""
    logger = logging.getLogger(__name__)
    logger.info(f"Shutting down {len(blocks)} unit(s)...")

    for block in blocks:
        try:
            await block.stop()
        except Exception as e:
            logger.error(f"Error stopping block '{block.name}': {e}")

    logger.info("All blocks stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}")

    # Run async shutdown
    loop = asyncio.get_event_loop()
    if running_blocks:
        loop.create_task(shutdown_units(running_blocks))

    sys.exit(0)


@app.command()
def run(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
    block_name: Optional[str] = typer.Option(
        None, "--block", "-u", help="Specific block to run (if config has multiple)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """
    Run an arroyo block from a configuration file.

    Examples:

        # Run a single block from config
        arroyo run pipeline.yaml

        # Run a specific block from multi-unit config
        arroyo run config.yaml --block data_processor

        # Run with verbose logging
        arroyo run pipeline.yaml --verbose
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
        if block_name:
            logger.info(f"Loading block '{block_name}' from {config_file}")
            block = load_block_from_yaml(config_file, block_name)
            blocks = [block]
        else:
            logger.info(f"Loading blocks from {config_file}")
            blocks = load_blocks_from_yaml(config_file)

        # Add to global list for signal handling
        running_blocks.extend(blocks)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run blocks using extracted business logic
        asyncio.run(run_units_async(blocks, logger))

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

        arroyo validate pipeline.yaml
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
        blocks = load_blocks_from_yaml(config_file)

        # Use extracted business logic
        validate_units_info(blocks, logger)

        typer.echo("\nConfiguration is valid! ✓")

    except ConfigurationError as e:
        logger.error(f"✗ Configuration error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"✗ Validation error: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def list_blocks(
    config_file: str = typer.Argument(..., help="Path to YAML configuration file"),
):
    """
    List all blocks defined in a configuration file.

    Example:

        arroyo list-blocks pipeline.yaml
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
        blocks = load_blocks_from_yaml(config_file)

        typer.echo(f"\nUnits in {config_file}:\n")

        for i, block in enumerate(blocks, 1):
            info = format_block_info(block)
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
