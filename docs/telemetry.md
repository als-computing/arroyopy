# OpenTelemetry and Prometheus Monitoring

Arroyopy includes built-in support for distributed tracing with OpenTelemetry/Jaeger and metrics with Prometheus.

## Features

### 1. Jaeger Distributed Tracing

The `@traced` decorator allows you to create Jaeger spans for any function:

```python
from arroyopy import traced, Operator

class MyOperator(Operator):
    @traced(span_name="custom_process", attributes={"version": "1.0"})
    async def process(self, message):
        # Your processing logic
        return message
```

The decorator automatically:
- Creates a span for the function execution
- Records function metadata (name, module)
- Captures exceptions and errors
- Works with both sync and async functions
- Supports nested spans for better trace visualization

### 2. Prometheus Metrics

Metrics are automatically collected for all listeners and operators:

#### Listener Metrics
- **`arroyopy_messages_received_total`** (Counter): Total messages received by each listener
- **`arroyopy_messages_per_second`** (Gauge): Current message rate per listener type

#### Operator Metrics
- **`arroyopy_processing_seconds`** (Histogram): Distribution of processing times
- **`arroyopy_avg_processing_seconds`** (Gauge): Running average of processing time per operator type

All metrics are labeled by type (listener class name or operator class name).

## Setup

### 1. Install Dependencies

The required dependencies are included in the main package:

```bash
pip install arroyopy
```

Or with pixi:

```bash
pixi install
```

### 2. Initialize Tracing (Optional)

Initialize OpenTelemetry tracing at application startup:

```python
from arroyopy import init_telemetry

# Initialize with default settings
init_telemetry()

# Or customize settings
init_telemetry(
    service_name="my-app",
    jaeger_host="jaeger.example.com",
    jaeger_port=6831
)
```

If you don't call `init_telemetry()`, it will be automatically initialized with default settings when the first `@traced` decorator is used.

### 3. Start Jaeger (for viewing traces)

```bash
# Using Docker
docker run -d \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Access UI at http://localhost:16686
```

### 4. Expose Prometheus Metrics

Add a metrics endpoint to your application:

```python
from prometheus_client import start_http_server

# Start metrics server on port 8000
start_http_server(8000)

# Metrics available at http://localhost:8000/metrics
```

## Usage Examples

### Basic Tracing

```python
from arroyopy import traced

@traced()  # Use function name as span name
async def process_data(data):
    return transform(data)

@traced(span_name="validate_input")  # Custom span name
def validate(data):
    return is_valid(data)
```

### Custom Attributes

```python
@traced(
    span_name="complex_operation",
    attributes={
        "version": "2.0",
        "environment": "production"
    }
)
async def complex_operation(data):
    # Your logic here
    return result
```

### Nested Spans

```python
class DataProcessor(Operator):
    @traced(span_name="process_pipeline")
    async def process(self, message):
        # These create child spans
        data = await self._fetch_data(message)
        result = await self._transform_data(data)
        return result

    @traced(span_name="fetch_data")
    async def _fetch_data(self, message):
        # Fetch logic
        return data

    @traced(span_name="transform_data")
    async def _transform_data(self, data):
        # Transform logic
        return result
```

### Monitoring with Prometheus

```python
from prometheus_client import start_http_server
from arroyopy import get_metrics_tracker

# Start metrics server
start_http_server(8000)

# Metrics are automatically collected by listeners and operators
# No additional code needed!

# Access metrics at http://localhost:8000/metrics
```

## Querying Metrics in Prometheus

Example PromQL queries:

```promql
# Message rate by listener type
arroyopy_messages_per_second{listener_type="RedisListener"}

# Average processing time by operator
arroyopy_avg_processing_seconds{operator_type="MyOperator"}

# 95th percentile processing time
histogram_quantile(0.95, arroyopy_processing_seconds_bucket)

# Total messages received
sum(arroyopy_messages_received_total)
```

## Architecture

### Automatic Metrics Collection

Metrics are collected automatically:

1. **Listeners**: Each time a message is received, the `MetricsTracker` records:
   - Message count (incremented)
   - Message rate (calculated every second)

2. **Operators**: Each time `process()` is called, timing is captured:
   - Start time before processing
   - End time after processing
   - Duration recorded in histogram and used for average calculation

### Tracing Flow

1. `@traced` decorator wraps functions
2. On function call, a span is started
3. Function executes (can call other traced functions, creating nested spans)
4. On completion/error, span is ended with status and attributes
5. Spans are batched and exported to Jaeger

## Configuration

### Environment Variables

You can configure tracing via environment variables:

```bash
# Jaeger configuration
export JAEGER_AGENT_HOST=localhost
export JAEGER_AGENT_PORT=6831
export OTEL_SERVICE_NAME=my-arroyopy-app
```

### Programmatic Configuration

```python
from arroyopy import init_telemetry

init_telemetry(
    service_name="my-app",
    jaeger_host="localhost",
    jaeger_port=6831
)
```

## Best Practices

1. **Initialize once**: Call `init_telemetry()` at application startup
2. **Use meaningful span names**: Make traces easier to understand
3. **Add context with attributes**: Include relevant metadata in spans
4. **Don't over-trace**: Focus on important operations, not every function
5. **Monitor metrics**: Set up alerts on processing time and message rates
6. **Use labels wisely**: Avoid high-cardinality labels in Prometheus

## Troubleshooting

### Traces not appearing in Jaeger

- Verify Jaeger is running: `curl http://localhost:16686`
- Check Jaeger agent connection: host and port are correct
- Ensure `init_telemetry()` was called
- Look for OpenTelemetry errors in logs

### Metrics not updating

- Verify Prometheus scrape endpoint is accessible
- Check that listeners/operators are actually processing messages
- Confirm `start_http_server()` was called
- Check for errors in application logs

### Performance Impact

- Tracing has minimal overhead (~1-5% in most cases)
- Metrics collection is very lightweight
- Batched exports reduce network overhead
- Consider sampling in high-throughput scenarios

## Integration with Monitoring Systems

### Grafana Dashboards

Create dashboards using Prometheus data source:

```promql
# Panel: Message Rate
arroyopy_messages_per_second

# Panel: Processing Time
arroyopy_avg_processing_seconds

# Panel: Throughput
rate(arroyopy_messages_received_total[5m])
```

### Alerts

Example Prometheus alerts:

```yaml
groups:
  - name: arroyopy
    rules:
      - alert: HighProcessingTime
        expr: arroyopy_avg_processing_seconds > 1.0
        for: 5m
        annotations:
          summary: "High processing time detected"

      - alert: LowMessageRate
        expr: arroyopy_messages_per_second < 10
        for: 5m
        annotations:
          summary: "Message rate dropped"
```

## Examples

See [telemetry_example.py](../examples/telemetry_example.py) for complete working examples.
