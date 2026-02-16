"""Demo of generic telemetry decorators."""

import asyncio
import random
import time

from arroyopy.otlp import setup_telemetry, trace_operation, traced

# Setup telemetry first
setup_telemetry(service_name="telemetry-demo")


# Basic usage - automatic tracing and metrics
@traced()
def calculate_sum(a: int, b: int) -> int:
    """Simple function with automatic telemetry."""
    time.sleep(random.uniform(0.01, 0.05))  # Simulate work
    return a + b


# Custom span name and attributes
@traced(span_name="math.multiply", attributes={"operation": "multiply"})
def multiply(a: int, b: int) -> int:
    """Function with custom span name and attributes."""
    time.sleep(random.uniform(0.01, 0.05))
    return a * b


# Record arguments and result
@traced(record_args=True, record_result=True)
def divide(a: float, b: float) -> float:
    """Function that records args and results."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


# Async function support
@traced(attributes={"async": "true"})
async def fetch_data(item_id: int) -> dict:
    """Async function with telemetry."""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    return {"id": item_id, "value": random.randint(1, 100)}


# Complex operation with context manager
def process_batch(items: list[int]):
    """Process a batch with manual span control."""
    with trace_operation("batch.process", {"batch.size": len(items)}) as span:
        results = []
        for i, item in enumerate(items):
            # You can add attributes dynamically
            if i % 10 == 0:
                span.set_attribute("items.processed", i)

            result = calculate_sum(item, 10)
            results.append(result)

        span.set_attribute("items.total", len(results))
        return results


async def main():
    """Run demo operations."""
    print("Running telemetry decorator demo...")
    print("View traces at: http://localhost:16686")
    print("View metrics at: http://localhost:3000")
    print()

    # Sync operations
    print("Sync operations:")
    for i in range(5):
        result = calculate_sum(i, i * 2)
        print(f"  calculate_sum({i}, {i*2}) = {result}")

    for i in range(3):
        result = multiply(i + 1, i + 2)
        print(f"  multiply({i+1}, {i+2}) = {result}")

    # Operation with args/result recording
    try:
        result = divide(10, 2)
        print(f"  divide(10, 2) = {result}")
        divide(10, 0)  # Will fail - trace will record exception
    except ValueError as e:
        print(f"  divide(10, 0) failed: {e}")

    # Async operations
    print("\nAsync operations:")
    tasks = [fetch_data(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    for result in results:
        print(f"  fetched: {result}")

    # Batch processing with context manager
    print("\nBatch processing:")
    batch = list(range(20))
    process_batch(batch)
    print(f"  Processed {len(batch)} items")

    print("\n✓ Demo complete! Check Jaeger and Grafana for traces and metrics.")


if __name__ == "__main__":
    asyncio.run(main())
