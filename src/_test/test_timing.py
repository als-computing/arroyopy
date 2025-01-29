import time

import pytest

from arroyopy.timing import timer


def test_timing_decorator():
    @timer
    def sample_function():
        time.sleep(0.1)
        return "done"

    result = sample_function()
    assert result == "done"
    assert "sample_function" in timer.current_event_times
    assert timer.current_event_times["sample_function"] == pytest.approx(
        0.1, abs=0.3
    )  # really slow for macox CI


def test_end_event():
    @timer
    def sample_function():
        time.sleep(0.1)
        return "done"

    @timer
    def sample_function2():
        time.sleep(0.1)
        return "done"

    sample_function()
    sample_function2()
    assert len(timer.current_event_times) == 2
    assert timer.current_event_times["sample_function"] is not None
    assert timer.current_event_times["sample_function2"] is not None
    timer.end_event()
    assert len(timer.current_event_times) == 0


def test_reset():
    @timer
    def sample_function():
        time.sleep(0.1)
        return "done"

    sample_function()
    sample_function()
    timer.end_event()
    timer.reset()
    assert len(timer.current_event_times) == 0
    assert timer.current_event_times == {}
    assert timer.events == []


if __name__ == "__main__":
    pytest.main()
