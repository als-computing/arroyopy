"""OpenTelemetry and Prometheus monitoring for Arroyopy."""

import functools
import logging
import time
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
MESSAGE_COUNTER = Counter(
    "arroyopy_messages_received_total",
    "Total number of messages received by listeners",
    ["listener_type"],
)

MESSAGE_RATE = Gauge(
    "arroyopy_messages_per_second",
    "Messages per second processed by listeners",
    ["listener_type"],
)

PROCESSING_TIME = Histogram(
    "arroyopy_processing_seconds",
    "Time spent processing messages in operators",
    ["operator_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

PROCESSING_TIME_SUMMARY = Gauge(
    "arroyopy_avg_processing_seconds",
    "Average time to process messages in operators",
    ["operator_type"],
)

# OpenTelemetry setup
_tracer_provider: Optional[TracerProvider] = None
_tracer: Optional[trace.Tracer] = None


def init_telemetry(
    service_name: str = "arroyopy",
    otlp_endpoint: str = "http://localhost:4317",
) -> None:
    """Initialize OpenTelemetry tracing with OTLP exporter.

    Parameters
    ----------
    service_name : str
        Name of the service for tracing
    otlp_endpoint : str
        OTLP endpoint URL (default: http://localhost:4317 for Jaeger)
        For Jaeger: use http://localhost:4317
        Can also be configured via OTEL_EXPORTER_OTLP_ENDPOINT env var
    """
    global _tracer_provider, _tracer

    resource = Resource(attributes={"service.name": service_name})
    _tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # Use insecure connection for local development
    )

    _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(_tracer_provider)
    _tracer = trace.get_tracer(__name__)

    logger.info(f"OpenTelemetry initialized with OTLP exporter at {otlp_endpoint}")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer, initializing if needed."""
    global _tracer
    if _tracer is None:
        init_telemetry()
    return _tracer


def traced(span_name: Optional[str] = None, attributes: Optional[dict] = None):
    """Decorator to create a Jaeger span for a function.

    Parameters
    ----------
    span_name : str, optional
        Name for the span. If not provided, uses the function name.
    attributes : dict, optional
        Additional attributes to add to the span.

    Examples
    --------
    >>> @traced()
    ... async def process_message(msg):
    ...     # Processing logic
    ...     pass

    >>> @traced(span_name="custom_operation", attributes={"version": "1.0"})
    ... def custom_function():
    ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            name = span_name or func.__name__
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            tracer = get_tracer()
            name = span_name or func.__name__
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class MetricsTracker:
    """Helper class to track metrics for listeners and operators."""

    def __init__(self):
        self._message_counts = {}
        self._last_update_time = {}
        self._processing_times = {}
        self._processing_counts = {}

    def record_message(self, listener_type: str) -> None:
        """Record a message received by a listener."""
        MESSAGE_COUNTER.labels(listener_type=listener_type).inc()

        # Update message rate calculation
        current_time = time.time()
        if listener_type not in self._message_counts:
            self._message_counts[listener_type] = 0
            self._last_update_time[listener_type] = current_time

        self._message_counts[listener_type] += 1

        # Update rate every second
        time_diff = current_time - self._last_update_time[listener_type]
        if time_diff >= 1.0:
            rate = self._message_counts[listener_type] / time_diff
            MESSAGE_RATE.labels(listener_type=listener_type).set(rate)
            self._message_counts[listener_type] = 0
            self._last_update_time[listener_type] = current_time

    def record_processing_time(self, operator_type: str, duration: float) -> None:
        """Record processing time for an operator."""
        PROCESSING_TIME.labels(operator_type=operator_type).observe(duration)

        # Calculate running average
        if operator_type not in self._processing_times:
            self._processing_times[operator_type] = 0.0
            self._processing_counts[operator_type] = 0

        self._processing_times[operator_type] += duration
        self._processing_counts[operator_type] += 1

        avg_time = (
            self._processing_times[operator_type]
            / self._processing_counts[operator_type]
        )
        PROCESSING_TIME_SUMMARY.labels(operator_type=operator_type).set(avg_time)


# Global metrics tracker instance
_metrics_tracker = MetricsTracker()


def get_metrics_tracker() -> MetricsTracker:
    """Get the global metrics tracker instance."""
    return _metrics_tracker
