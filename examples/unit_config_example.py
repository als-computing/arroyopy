"""
Example: Using arroyo Units with configuration files

This example demonstrates how to:
1. Create a configuration file for an arroyo unit
2. Load and run the unit programmatically
3. Use the CLI to run units
"""
import logging

from arroyopy import load_unit_from_yaml, load_units_from_yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Load and run a single unit programmatically
async def run_from_config():
    """Load a unit from a YAML file and run it."""
    logger.info("Loading unit from configuration...")

    # Load the unit
    unit = load_unit_from_yaml("examples/config/simple_pipeline.yaml")

    logger.info(f"Loaded unit: {unit.name}")
    logger.info(f"Operator: {unit.operator.__class__.__name__}")
    logger.info(f"Listeners: {len(unit.listeners)}")
    logger.info(f"Publishers: {len(unit.publishers)}")

    # Start the unit
    # await unit.start()  # Uncomment to actually run


# Example 2: Load specific unit from multi-unit config
async def run_specific_unit():
    """Load a specific unit by name from a config file."""
    logger.info("Loading specific unit from multi-unit config...")

    unit = load_unit_from_yaml(
        "examples/config/multi_unit.yaml", unit_name="data_ingestion"
    )

    logger.info(f"Loaded unit: {unit.name}")
    # await unit.start()  # Uncomment to actually run


# Example 3: Load all units
async def run_all_units():
    """Load all units from a config file."""
    logger.info("Loading all units...")

    units = load_units_from_yaml("examples/config/multi_unit.yaml")

    for unit in units:
        logger.info(f"Found unit: {unit.name}")
        logger.info(f"  - Operator: {unit.operator.__class__.__name__}")
        logger.info(f"  - Listeners: {len(unit.listeners)}")
        logger.info(f"  - Publishers: {len(unit.publishers)}")

    # To run all units concurrently:
    # tasks = [unit.start() for unit in units]
    # await asyncio.gather(*tasks)


# Example 4: Programmatic configuration
async def programmatic_example():
    """Create a unit programmatically without YAML."""

    # This would require actual operator/listener/publisher implementations
    # operator = MyOperator()
    # listener = MyListener(operator)
    # publisher = MyPublisher()
    # unit = Unit(
    #     name='programmatic_unit',
    #     operator=operator,
    #     listeners=[listener],
    #     publishers=[publisher]
    # )
    # await unit.start()

    logger.info("See the code for programmatic unit creation example")


def main():
    """Run the examples."""
    print("\n=== Arroyo Configuration Examples ===\n")

    print("1. Load and inspect unit from config")
    # asyncio.run(run_from_config())

    print("\n2. Load specific unit from multi-unit config")
    # asyncio.run(run_specific_unit())

    print("\n3. Load all units")
    # asyncio.run(run_all_units())

    print("\n4. Programmatic configuration")
    # asyncio.run(programmatic_example())

    print("\n=== CLI Usage ===\n")
    print("To run a unit from the command line:")
    print("  arroyo-run examples/config/simple_pipeline.yaml")
    print("\nTo validate a configuration:")
    print("  arroyo-run validate examples/config/simple_pipeline.yaml")
    print("\nTo list units in a config file:")
    print("  arroyo-run list-units examples/config/multi_unit.yaml")
    print("\nTo run a specific unit:")
    print("  arroyo-run examples/config/multi_unit.yaml --unit data_ingestion")
    print()


if __name__ == "__main__":
    main()
