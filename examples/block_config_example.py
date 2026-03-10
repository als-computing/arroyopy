"""
Example: Using arroyo Units with configuration files

This example demonstrates how to:
1. Create a configuration file for an arroyo unit
2. Load and run the block programmatically
3. Use the CLI to run blocks
"""
import logging

from arroyopy import load_block_from_yaml, load_blocks_from_yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Load and run a single block programmatically
async def run_from_config():
    """Load a block from a YAML file and run it."""
    logger.info("Loading block from configuration...")

    # Load the unit
    block = load_block_from_yaml("examples/config/simple_pipeline.yaml")

    logger.info(f"Loaded unit: {block.name}")
    logger.info(f"Operator: {block.operator.__class__.__name__}")
    logger.info(f"Listeners: {len(block.listeners)}")
    logger.info(f"Publishers: {len(block.publishers)}")

    # Start the unit
    # await block.start()  # Uncomment to actually run


# Example 2: Load specific block from multi-unit config
async def run_specific_unit():
    """Load a specific block by name from a config file."""
    logger.info("Loading specific block from multi-unit config...")

    block = load_block_from_yaml(
        "examples/config/multi_block.yaml", block_name="data_ingestion"
    )

    logger.info(f"Loaded unit: {block.name}")
    # await block.start()  # Uncomment to actually run


# Example 3: Load all blocks
async def run_all_units():
    """Load all blocks from a config file."""
    logger.info("Loading all blocks...")

    blocks = load_blocks_from_yaml("examples/config/multi_block.yaml")

    for block in blocks:
        logger.info(f"Found unit: {block.name}")
        logger.info(f"  - Operator: {block.operator.__class__.__name__}")
        logger.info(f"  - Listeners: {len(block.listeners)}")
        logger.info(f"  - Publishers: {len(block.publishers)}")

    # To run all blocks concurrently:
    # tasks = [block.start() for block in blocks]
    # await asyncio.gather(*tasks)


# Example 4: Programmatic configuration
async def programmatic_example():
    """Create a block programmatically without YAML."""

    # This would require actual operator/listener/publisher implementations
    # operator = MyOperator()
    # listener = MyListener(operator)
    # publisher = MyPublisher()
    # block = Block(
    #     name='programmatic_unit',
    #     operator=operator,
    #     listeners=[listener],
    #     publishers=[publisher]
    # )
    # await block.start()

    logger.info("See the code for programmatic block creation example")


def main():
    """Run the examples."""
    print("\n=== Arroyo Configuration Examples ===\n")

    print("1. Load and inspect block from config")
    # asyncio.run(run_from_config())

    print("\n2. Load specific block from multi-unit config")
    # asyncio.run(run_specific_unit())

    print("\n3. Load all blocks")
    # asyncio.run(run_all_units())

    print("\n4. Programmatic configuration")
    # asyncio.run(programmatic_example())

    print("\n=== CLI Usage ===\n")
    print("To run a block from the command line:")
    print("  arroyo run examples/config/simple_pipeline.yaml")
    print("\nTo validate a configuration:")
    print("  arroyo validate examples/config/simple_pipeline.yaml")
    print("\nTo list blocks in a config file:")
    print("  arroyo list-blocks examples/config/multi_block.yaml")
    print("\nTo run a specific unit:")
    print("  arroyo run examples/config/multi_block.yaml --block data_ingestion")
    print()


if __name__ == "__main__":
    main()
