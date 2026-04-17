"""Example showing how to expose Prometheus metrics endpoint.

This example demonstrates:
1. Starting a Prometheus metrics HTTP server
2. Running an operator with automatic metrics collection
3. Querying metrics from the /metrics endpoint
"""

import asyncio
import logging
import random

from prometheus_client import start_http_server

from arroyopy import Operator, init_telemetry, traced
from arroyopy.schemas import Message

logging.basicConfig(level=logging.INFO)


class MetricsExampleOperator(Operator):
    """Example operator that processes messages with metrics collection."""

    @traced(span_name="process_message")
    async def process(self, message: Message) -> Message:
        """Process message with variable timing to demonstrate metrics."""
        # Simulate variable processing time
        processing_time = random.uniform(0.01, 0.5)
        await asyncio.sleep(processing_time)
        return message


async def simulate_message_processing():
    """Simulate processing messages to generate metrics."""
    operator = MetricsExampleOperator()

    # Simulate processing 100 messages
    for i in range(100):
        message = Message(data={"id": i, "value": f"message_{i}"})
        await operator.listener_queue.put(message)

        # Start operator processing in background
        if i == 0:
            asyncio.create_task(operator.start())

        # Small delay between messages to show rate variation
        await asyncio.sleep(random.uniform(0.05, 0.2))

    print("Finished processing messages")


async def main():
    """Main function to demonstrate Prometheus metrics."""
    # Initialize OpenTelemetry (optional, but good for complete observability)
    init_telemetry(service_name="prometheus-example")

    # Start Prometheus HTTP server on port 8000
    # Metrics will be available at http://localhost:8000/metrics
    print("Starting Prometheus metrics server on port 8000...")
    start_http_server(8000)
    print("Metrics available at: http://localhost:8000/metrics")

    print("\nAvailable metrics:")
    print("- arroyopy_messages_received_total: Total messages received")
    print("- arroyopy_messages_per_second: Current message rate")
    print("- arroyopy_processing_seconds: Processing time histogram")
    print("- arroyopy_avg_processing_seconds: Average processing time")

    print("\nStarting message processing...")
    print("(Open http://localhost:8000/metrics in a browser to see metrics)\n")

    # Simulate message processing
    await simulate_message_processing()

    # Keep server running for a bit to allow metric inspection
    print("\nMetrics server still running. Check http://localhost:8000/metrics")
    print("Press Ctrl+C to stop...")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    asyncio.run(main())
