import functools
import logging
import time

import pandas as pd

logger = logging.getLogger(__name__)

effective_level = logger.getEffectiveLevel()

class EventTimingDecorator:
    """
    Decorator to time functions and output the results in a pandas DataFrame.

    This assumes within a single Event, there will be multiple calls to different functions.
    When a new event starts, call `end_event` to store the timings and reset the timings for the next event.
    When all events are done the timings can be accessed as a DataFrame using the `timing_dataframe` property.
    After all events are done, call `reset` to clear all timings for the next event.
    """


    def __init__(self):
        self.current_event_times = {}
        self.events = []

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            self.current_event_times[func.__name__] = duration
            if effective_level == logging.DEBUG:
                (f"{func.__name__} took {duration:.4f} seconds")
            return result

        return wrapper

    def end_event(self):
        if self.current_event_times:
            self.events.append(self.current_event_times)
        self.current_event_times = {}

    @property
    def timing_dataframe(self):
        return pd.DataFrame(self.current_event_times)

    def reset(self):
        self.current_event_times = {}
        self.events = []

timer = EventTimingDecorator()