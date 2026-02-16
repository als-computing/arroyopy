"""OpenTelemetry setup and utilities for arroyopy."""

import functools
import inspect
import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

# Global flag to track initialization
_initialized = False


def setup_telemetry(
    service_name: str = "arroyopy",
    otlp_endpoint: Optional[str] = None,
    insecure: bool = True,
) -> tuple[trace.Tracer, metrics.Meter]:
    """
    Setup OpenTelemetry tracing and metrics.

    Parameters
    ----------
    service_name : str
        Name of the service for telemetry identification
    otlp_endpoint : str, optional
        OTLP collector endpoint. Defaults to env var OTEL_EXPORTER_OTLP_ENDPOINT
        or localhost:4317
    insecure : bool
        Whether to use insecure gRPC connection (default: True for local development)

    Returns
    -------
    tuple[Tracer, Meter]
        Configured tracer and meter instances
    """
    global _initialized

    if _initialized:
        logger.debug("Telemetry already initialized, returning existing instances")
        return trace.get_tracer(__name__), metrics.get_meter(__name__)

    # Determine endpoint
    if otlp_endpoint is None:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")

    logger.info(f"Initializing OpenTelemetry with endpoint: {otlp_endpoint}")

    # Create resource with service name
    resource = Resource.create({"service.name": service_name})

    # Setup Tracing
    trace_provider = TracerProvider(resource=resource)
    trace_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    # Setup Metrics
    metric_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=15000,  # Export every 15 seconds
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)

    _initialized = True
    logger.info("OpenTelemetry initialization complete")

    return trace.get_tracer(__name__), metrics.get_meter(__name__)


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance.

    Parameters
    ----------
    name : str
        Name of the tracer (typically __name__ of the module)

    Returns
    -------
    Tracer
        OpenTelemetry tracer instance
    """
    return trace.get_tracer(name)


def get_meter(name: str = __name__) -> metrics.Meter:
    """
    Get a meter instance.

    Parameters
    ----------
    name : str
        Name of the meter (typically __name__ of the module)

    Returns
    -------
    Meter
        OpenTelemetry meter instance
    """
    return metrics.get_meter(name)


def traced(
    span_name: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
    record_args: bool = False,
    record_result: bool = False,
) -> Callable:
    """
    Decorator to automatically trace a function with metrics.

    Creates a trace span and records duration histogram for the decorated function.
    Automatically handles exceptions and async functions.

    Parameters
    ----------
    span_name : str, optional
        Custom span name. Defaults to module.function_name
    attributes : dict, optional
        Additional attributes to add to the span
    record_args : bool
        Whether to record function arguments as span attributes (default: False)
    record_result : bool
        Whether to record return value as span attribute (default: False)

    Returns
    -------
    Callable
        Decorated function

    Examples
    --------
    >>> @traced()
    ... def my_function(x, y):
    ...     return x + y

    >>> @traced(span_name="custom.operation", attributes={"operation": "add"})
    ... async def async_function(value):
    ...     return await process(value)

    >>> @traced(record_args=True, record_result=True)
    ... def calculate(a, b):
    ...     return a * b
    """

    def decorator(func: Callable) -> Callable:
        tracer = get_tracer(func.__module__)
        meter = get_meter(func.__module__)

        # Create metrics (names must be < 63 chars)
        duration_histogram = meter.create_histogram(
            "function.duration",
            description=f"Duration of {func.__name__} calls",
            unit="s",
        )
        call_counter = meter.create_counter(
            "function.calls",
            description=f"Number of {func.__name__} calls",
        )

        # Determine span name
        default_span_name = f"{func.__module__}.{func.__name__}"
        actual_span_name = span_name or default_span_name

        if inspect.iscoroutinefunction(func):
            # Async version
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_attributes = dict(attributes) if attributes else {}
                span_attributes["function.name"] = func.__name__
                span_attributes["function.module"] = func.__module__

                if record_args:
                    # Record positional args
                    for i, arg in enumerate(args):
                        span_attributes[f"arg.{i}"] = str(arg)
                    # Record keyword args
                    for key, value in kwargs.items():
                        span_attributes[f"arg.{key}"] = str(value)

                with tracer.start_as_current_span(actual_span_name) as span:
                    for key, value in span_attributes.items():
                        span.set_attribute(key, value)

                    start_time = time.time()
                    success = True
                    try:
                        result = await func(*args, **kwargs)

                        if record_result and result is not None:
                            span.set_attribute("result", str(result))

                        return result
                    except Exception as e:
                        success = False
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                    finally:
                        duration = time.time() - start_time
                        status = "success" if success else "error"
                        metric_attributes = {
                            "function": func.__name__,
                            "status": status,
                        }
                        duration_histogram.record(duration, metric_attributes)
                        call_counter.add(1, metric_attributes)

            return async_wrapper
        else:
            # Sync version
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_attributes = dict(attributes) if attributes else {}
                span_attributes["function.name"] = func.__name__
                span_attributes["function.module"] = func.__module__

                if record_args:
                    # Record positional args
                    for i, arg in enumerate(args):
                        span_attributes[f"arg.{i}"] = str(arg)
                    # Record keyword args
                    for key, value in kwargs.items():
                        span_attributes[f"arg.{key}"] = str(value)

                with tracer.start_as_current_span(actual_span_name) as span:
                    for key, value in span_attributes.items():
                        span.set_attribute(key, value)

                    start_time = time.time()
                    success = True
                    try:
                        result = func(*args, **kwargs)

                        if record_result and result is not None:
                            span.set_attribute("result", str(result))

                        return result
                    except Exception as e:
                        success = False
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise
                    finally:
                        duration = time.time() - start_time
                        status = "success" if success else "error"
                        metric_attributes = {
                            "function": func.__name__,
                            "status": status,
                        }
                        duration_histogram.record(duration, metric_attributes)
                        call_counter.add(1, metric_attributes)

            return sync_wrapper

    return decorator


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[dict[str, Any]] = None,
    record_duration: bool = True,
):
    """
    Context manager for tracing a code block with metrics.

    Parameters
    ----------
    operation_name : str
        Name of the operation/span
    attributes : dict, optional
        Attributes to add to the span
    record_duration : bool
        Whether to record duration as a metric (default: True)

    Yields
    ------
    Span
        The active span for adding additional attributes

    Examples
    --------
    >>> with trace_operation("database.query", {"table": "users"}):
    ...     results = db.query("SELECT * FROM users")

    >>> with trace_operation("process.batch") as span:
    ...     for item in batch:
    ...         process(item)
    ...         span.set_attribute("items.processed", count)
    """
    tracer = get_tracer()
    meter = get_meter()

    span_attributes = dict(attributes) if attributes else {}

    # Create histogram for this operation type if recording duration
    if record_duration:
        duration_histogram = meter.create_histogram(
            f"{operation_name}.duration",
            description=f"Duration of {operation_name}",
            unit="s",
        )

    with tracer.start_as_current_span(operation_name) as span:
        for key, value in span_attributes.items():
            span.set_attribute(key, value)

        start_time = time.time()
        success = True
        try:
            yield span
        except Exception as e:
            success = False
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            if record_duration:
                duration = time.time() - start_time
                status = "success" if success else "error"
                duration_histogram.record(duration, {"status": status})
