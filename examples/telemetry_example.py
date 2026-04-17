"""Example demonstrating OpenTelemetry and Prometheus metrics in Arroyopy.

This example shows:
1. How to use the @traced decorator for Jaeger spans
2. How metrics are automatically collected for listeners and operators
3. How to initialize OpenTelemetry/Jaeger tracing
"""

import asyncio
import logging

from arroyopy import Operator, init_telemetry, traced
from arroyopy.schemas import Message

logging.basicConfig(level=logging.INFO)


class ExampleOperator(Operator):
    """Example operator that uses the @traced decorator."""

    @traced(span_name="process_message", attributes={"component": "example"})
    async def process(self, message: Message) -> Message:
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
        # Simulate some processing
        await asyncio.sleep(0.1)
        return message


class ComplexOperator(Operator):
    """Operator with multiple traced methods."""

    async def process(self, message: Message) -> Message:
        """Main processing method that calls other traced methods."""
        # These will create nested spans in Jaeger
        validated = await self._validate_message(message)
        transformed = await self._transform_message(validated)
        enriched = await self._enrich_message(transformed)
        return enriched

    @traced(span_name="validate")
    async def _validate_message(self, message: Message) -> Message:
        """Validate the message structure."""
        # Validation logic
        await asyncio.sleep(0.01)
        return message

    @traced(span_name="transform")
    async def _transform_message(self, message: Message) -> Message:
        """Transform the message data."""
        # Transformation logic
        await asyncio.sleep(0.02)
        return message

    @traced(span_name="enrich")
    async def _enrich_message(self, message: Message) -> Message:
        """Enrich the message with additional data."""
        # Enrichment logic
        await asyncio.sleep(0.03)
        return message


def main():
    """Example usage of telemetry features."""
    # Initialize OpenTelemetry with Jaeger
    # This should be done once at application startup
    init_telemetry(
        service_name="arroyopy-example",
        jaeger_host="localhost",  # Default Jaeger agent host
        jaeger_port=6831,  # Default Jaeger agent port
    )

    print("OpenTelemetry initialized!")
    print("\nMetrics are automatically collected:")
    print("- Listeners: messages_per_second (gauge)")
    print("- Operators: avg_time_to_process (gauge)")
    print("- All metrics are exported to Prometheus")

    print("\n@traced decorator usage:")
    print("- Creates Jaeger spans for functions")
    print("- Works with both sync and async functions")
    print("- Automatically records errors and exceptions")
    print("- Supports custom span names and attributes")

    print("\nTo view traces:")
    print(
        "1. Start Jaeger: docker run -d -p 6831:6831/udp -p 16686:16686 jaegertracing/all-in-one"
    )
    print("2. Open http://localhost:16686")
    print("3. Select 'arroyopy-example' service")

    print("\nTo view Prometheus metrics:")
    print("1. Start Prometheus server (configure scrape endpoint)")
    print("2. Metrics available at /metrics endpoint")
    print("3. Query for:")
    print("   - arroyopy_messages_per_second")
    print("   - arroyopy_avg_processing_seconds")


if __name__ == "__main__":
    main()
