# OpenTelemetry Integration - Quick Reference

## What was added:

### 1. New Module: `telemetry.py`
- **`@traced` decorator**: Creates Jaeger spans for functions
- **`init_telemetry()`**: Initialize OpenTelemetry with Jaeger
- **`get_metrics_tracker()`**: Access the global metrics tracker
- **Automatic Prometheus metrics** for listeners and operators

### 2. Dependencies Added (pyproject.toml)
- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-jaeger`
- `prometheus-client`

### 3. Automatic Metrics Collection

#### Listeners (RedisListener, ZMQListener)
- **Messages per second** - Real-time message rate
- **Total messages received** - Cumulative counter
- Labeled by listener type (class name)

#### Operators
- **Average processing time** - Running average
- **Processing time histogram** - Full distribution
- Labeled by operator type (class name)

## Quick Start

### Use the @traced decorator:

```python
from arroyopy import traced, Operator

class MyOperator(Operator):
    @traced()  # Simple usage
    async def process(self, message):
        return message

    @traced(span_name="validate", attributes={"version": "1.0"})
    async def validate(self, data):
        return data
```

### Initialize tracing (optional):

```python
from arroyopy import init_telemetry

init_telemetry(
    service_name="my-app",
    otlp_endpoint="http://localhost:4317"
)
```

### Expose Prometheus metrics:

```python
from prometheus_client import start_http_server

# Start metrics server
start_http_server(8000)
# Metrics at http://localhost:8000/metrics
```

## Prometheus Metrics Available

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `arroyopy_messages_received_total` | Counter | Total messages received | listener_type |
| `arroyopy_messages_per_second` | Gauge | Current message rate | listener_type |
| `arroyopy_processing_seconds` | Histogram | Processing time distribution | operator_type |
| `arroyopy_avg_processing_seconds` | Gauge | Average processing time | operator_type |

## Files Created

1. **`src/arroyopy/telemetry.py`** - Main telemetry module
2. **`src/_test/test_telemetry.py`** - Unit tests
3. **`examples/telemetry_example.py`** - Usage examples
4. **`examples/prometheus_example.py`** - Metrics server example
5. **`docs/telemetry.md`** - Complete documentation

## Files Modified

1. **`pyproject.toml`** - Added dependencies
2. **`src/arroyopy/__init__.py`** - Exported telemetry functions
3. **`src/arroyopy/operator.py`** - Added processing time tracking
4. **`src/arroyopy/redis.py`** - Added message rate tracking
5. **`src/arroyopy/zmq.py`** - Added message rate tracking

## Next Steps

1. **Install new dependencies:**
   ```bash
   pixi install  # or pip install -e .
   ```

2. **Start observability stack:**
   ```bash
   # Option 1: Full stack (recommended) - Jaeger + Prometheus + Grafana
   docker-compose up -d

   # Option 2: Just Jaeger for tracing
   docker-compose up -d jaeger

   # Option 3: Using docker directly
   docker run -d -p 4317:4317 -p 16686:16686 jaegertracing/all-in-one
   ```

   **Access points:**
   - Jaeger UI: http://localhost:16686
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)

3. **Add metrics endpoint to your app:**
   ```python
   from prometheus_client import start_http_server
   start_http_server(8000)
   ```

4. **Use @traced decorator in your operators:**
   ```python
   @traced(span_name="my_process")
   async def process(self, message):
       # your code
   ```

See [DOCKER_SERVICES.md](DOCKER_SERVICES.md) for detailed docker-compose documentation.

## How It Works

### Automatic Collection
- **No code changes needed** for basic metrics
- Listeners automatically track message rates when messages are received
- Operators automatically track processing times when messages are processed
- All metrics exported to Prometheus automatically

### Manual Tracing
- Use `@traced` decorator for custom spans
- Supports nested spans
- Works with sync and async functions
- Automatically captures errors and exceptions

## Documentation

See [docs/telemetry.md](../docs/telemetry.md) for complete documentation including:
- Detailed usage examples
- Configuration options
- Prometheus query examples
- Grafana dashboard setup
- Troubleshooting guide
- Best practices
