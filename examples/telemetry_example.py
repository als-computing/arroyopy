"""Example demonstrating OpenTelemetry and Prometheus metrics in Arroyopy.

This example shows:
1. How to use the @traced decorator for Jaeger spans
2. How metrics are automatically collected for listeners and operators
3. How to initialize OpenTelemetry/Jaeger tracing
4. Running operators with actual message processing
"""

import asyncio
import logging
import random
from typing import Any

from prometheus_client import start_http_server

from arroyopy import Operator, init_telemetry, traced

logging.basicConfig(level=logging.INFO)


class ExampleOperator(Operator):
    """Example operator that uses the @traced decorator."""

    def __init__(self):
        super().__init__()
        self.processed_count = 0

    @traced(span_name="process_message", attributes={"component": "example"})
    async def process(self, message: Any) -> Any:
        """Process a message with automatic tracing and metrics.

        The @traced decorator automatically:
        - Creates a Jaeger span for this function
        - Adds custom attributes to the span
        - Records exceptions and errors
        - Tracks function execution time

        The Operator base class automatically:
        - Tracks processing time metrics
        - Calculates average processing time
        - Exports metrics to Prometheus
        """
        # Simulate some processing with variable time
        await asyncio.sleep(random.uniform(0.05, 0.15))

        self.processed_count += 1
        logger = logging.getLogger(__name__)
        logger.info(f"Processed message #{self.processed_count}: {message}")

        return message


class ComplexOperator(Operator):
    """Operator with multiple traced methods showing nested spans."""

    def __init__(self):
        super().__init__()
        self.processed_count = 0

    @traced(span_name="process_message")
    async def process(self, message: Any) -> Any:
        """Main processing method that calls other traced methods."""
        # These will create nested spans in Jaeger
        validated = await self._validate_message(message)
        transformed = await self._transform_message(validated)
        enriched = await self._enrich_message(transformed)

        self.processed_count += 1
        logger = logging.getLogger(__name__)
        logger.info(f"Complex operator processed message #{self.processed_count}")

        return enriched

    @traced(span_name="validate")
    async def _validate_message(self, message: Any) -> Any:
        """Validate the message structure."""
        # Validation logic
        await asyncio.sleep(0.01)
        return message

    @traced(span_name="transform")
    async def _transform_message(self, message: Any) -> Any:
        """Transform the message data."""
        # Transformation logic
        await asyncio.sleep(0.02)
        return message

    @traced(span_name="enrich")
    async def _enrich_message(self, message: Any) -> Any:
        """Enrich the message with additional data."""
        # Enrichment logic
        await asyncio.sleep(0.03)
        return message


async def simulate_messages(operator: Operator, num_messages: int = 20):
    """Simulate sending messages to an operator."""
    logger = logging.getLogger(__name__)

    for i in range(num_messages):
        # Just use a simple dict as the message data
        message = {
            "id": i,
            "value": f"test_message_{i}",
            "timestamp": asyncio.get_event_loop().time(),
        }
        await operator.notify(message)
        # Small delay between messages
        await asyncio.sleep(random.uniform(0.1, 0.3))

    logger.info(f"Sent {num_messages} messages to operator")


async def run_demo():
    """Run the telemetry demonstration."""
    logger = logging.getLogger(__name__)

    print("\n" + "=" * 70)
    print("Arroyopy Telemetry Demo")
    print("=" * 70)

    # Initialize OpenTelemetry
    init_telemetry(
        service_name="arroyopy-demo",
        otlp_endpoint="http://localhost:4317",
    )
    print("✓ OpenTelemetry initialized")

    # Start Prometheus metrics server
    print("✓ Starting Prometheus metrics server on port 8000")
    start_http_server(8000)
    print("  → Metrics available at: http://localhost:8000/metrics")

    print("\n" + "-" * 70)
    print("Running operators with message processing...")
    print("-" * 70 + "\n")

    # Create operators
    simple_operator = ExampleOperator()
    complex_operator = ComplexOperator()

    # Start operators in background
    simple_task = asyncio.create_task(simple_operator.start())
    complex_task = asyncio.create_task(complex_operator.start())

    # Simulate messages for simple operator
    logger.info("Sending messages to ExampleOperator...")
    await simulate_messages(simple_operator, num_messages=10)

    # Simulate messages for complex operator
    logger.info("Sending messages to ComplexOperator...")
    await simulate_messages(complex_operator, num_messages=10)

    # Let operators finish processing
    await asyncio.sleep(2)

    # Stop operators
    simple_operator.stop_requested = True
    complex_operator.stop_requested = True

    # Send final messages to trigger stop
    await simple_operator.notify({"stop": True})
    await complex_operator.notify({"stop": True})

    await asyncio.gather(simple_task, complex_task, return_exceptions=True)

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print("\nWhat just happened:")
    print("1. ✓ Processed 20 messages through 2 operators")
    print("2. ✓ Created Jaeger spans with @traced decorator")
    print("3. ✓ Collected Prometheus metrics automatically")
    print("\nView the results:")
    print("• Prometheus metrics: http://localhost:8000/metrics")
    print("  - Look for arroyopy_avg_processing_seconds")
    print("  - Look for arroyopy_processing_seconds_* (histogram buckets)")
    print("\n• Jaeger traces (if running):")
    print("  1. Start Jaeger: docker-compose up -d jaeger")
    print(
        "     (or: docker run -d -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one)"
    )
    print("  2. Open: http://localhost:16686")
    print("  3. Select service: arroyopy-demo")
    print("  4. Click 'Find Traces'")
    print("\nPress Ctrl+C to exit (metrics server will keep running)")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")


def main():
    """Entry point for the demo."""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
