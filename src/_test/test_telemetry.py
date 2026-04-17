"""Tests for OpenTelemetry and Prometheus telemetry."""

import asyncio
import time

import pytest

from arroyopy.telemetry import (
    MetricsTracker,
    get_metrics_tracker,
    get_tracer,
    init_telemetry,
    traced,
)


class TestTelemetryInit:
    """Test telemetry initialization."""

    def test_init_telemetry_default(self):
        """Test initialization with default parameters."""
        init_telemetry()
        tracer = get_tracer()
        assert tracer is not None

    def test_init_telemetry_custom(self):
        """Test initialization with custom parameters."""
        init_telemetry(
            service_name="test-service", jaeger_host="testhost", jaeger_port=6832
        )
        tracer = get_tracer()
        assert tracer is not None


class TestTracedDecorator:
    """Test the @traced decorator."""

    @pytest.mark.asyncio
    async def test_traced_async_function(self):
        """Test tracing an async function."""

        @traced()
        async def async_function():
            await asyncio.sleep(0.01)
            return "result"

        result = await async_function()
        assert result == "result"

    def test_traced_sync_function(self):
        """Test tracing a sync function."""

        @traced()
        def sync_function():
            return "sync_result"

        result = sync_function()
        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_traced_with_custom_name(self):
        """Test tracing with custom span name."""

        @traced(span_name="custom_span")
        async def custom_function():
            return "custom"

        result = await custom_function()
        assert result == "custom"

    @pytest.mark.asyncio
    async def test_traced_with_attributes(self):
        """Test tracing with custom attributes."""

        @traced(span_name="attr_span", attributes={"key": "value", "number": 42})
        async def attr_function():
            return "attrs"

        result = await attr_function()
        assert result == "attrs"

    @pytest.mark.asyncio
    async def test_traced_exception_handling(self):
        """Test that traced decorator handles exceptions."""

        @traced()
        async def failing_function():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await failing_function()

    def test_traced_sync_exception_handling(self):
        """Test that traced decorator handles exceptions in sync functions."""

        @traced()
        def failing_sync_function():
            raise RuntimeError("sync error")

        with pytest.raises(RuntimeError, match="sync error"):
            failing_sync_function()


class TestMetricsTracker:
    """Test the MetricsTracker class."""

    def test_metrics_tracker_singleton(self):
        """Test that get_metrics_tracker returns the same instance."""
        tracker1 = get_metrics_tracker()
        tracker2 = get_metrics_tracker()
        assert tracker1 is tracker2

    def test_record_message(self):
        """Test recording messages."""
        tracker = MetricsTracker()
        tracker.record_message("TestListener")
        # Should not raise any errors

    def test_record_processing_time(self):
        """Test recording processing time."""
        tracker = MetricsTracker()
        tracker.record_processing_time("TestOperator", 0.123)
        # Should not raise any errors

    def test_message_rate_calculation(self):
        """Test that message rate is calculated over time."""
        tracker = MetricsTracker()

        # Record some messages
        for _ in range(10):
            tracker.record_message("TestListener")

        # Should have rate data stored internally
        assert "TestListener" in tracker._message_counts

    def test_processing_time_average(self):
        """Test that average processing time is calculated."""
        tracker = MetricsTracker()

        # Record several processing times
        tracker.record_processing_time("TestOperator", 0.1)
        tracker.record_processing_time("TestOperator", 0.2)
        tracker.record_processing_time("TestOperator", 0.3)

        # Verify internal state
        assert "TestOperator" in tracker._processing_times
        assert tracker._processing_counts["TestOperator"] == 3
        # Average should be (0.1 + 0.2 + 0.3) / 3 = 0.2
        avg = tracker._processing_times["TestOperator"] / 3
        assert abs(avg - 0.2) < 0.001


class TestIntegration:
    """Integration tests for telemetry."""

    @pytest.mark.asyncio
    async def test_nested_spans(self):
        """Test that nested traced functions create nested spans."""

        @traced(span_name="outer")
        async def outer_function():
            result = await inner_function()
            return f"outer-{result}"

        @traced(span_name="inner")
        async def inner_function():
            return "inner"

        result = await outer_function()
        assert result == "outer-inner"

    @pytest.mark.asyncio
    async def test_metrics_and_tracing_together(self):
        """Test that metrics and tracing work together."""
        tracker = get_metrics_tracker()

        @traced(span_name="combined_test")
        async def traced_with_metrics():
            tracker.record_message("CombinedListener")
            start = time.perf_counter()
            await asyncio.sleep(0.01)
            duration = time.perf_counter() - start
            tracker.record_processing_time("CombinedOperator", duration)
            return "combined"

        result = await traced_with_metrics()
        assert result == "combined"
        assert "CombinedListener" in tracker._message_counts
        assert "CombinedOperator" in tracker._processing_times
