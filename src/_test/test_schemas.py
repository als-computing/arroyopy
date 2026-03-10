"""
Unit tests for the schemas module.
"""
import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from arroyopy.schemas import (
    DataFrameModel,
    Event,
    Message,
    NumpyArrayModel,
    PydanticMessage,
    Start,
    Stop,
)


def test_message_base_class():
    """Test Message base class instantiation."""
    message = Message()
    assert isinstance(message, Message)


def test_pydantic_message():
    """Test PydanticMessage instantiation."""
    message = PydanticMessage()
    assert isinstance(message, Message)
    assert isinstance(message, PydanticMessage)


def test_start_message():
    """Test Start message."""
    start = Start()
    assert isinstance(start, PydanticMessage)
    assert isinstance(start, Message)


def test_stop_message():
    """Test Stop message."""
    stop = Stop()
    assert isinstance(stop, PydanticMessage)
    assert isinstance(stop, Message)


def test_event_message():
    """Test Event message."""
    event = Event()
    assert isinstance(event, PydanticMessage)
    assert isinstance(event, Message)


def test_dataframe_model_valid():
    """Test DataFrameModel with valid DataFrame."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    model = DataFrameModel(df=df)
    assert isinstance(model.df, pd.DataFrame)
    pd.testing.assert_frame_equal(model.df, df)


def test_dataframe_model_invalid():
    """Test DataFrameModel with invalid input (not a DataFrame)."""
    with pytest.raises((ValidationError, TypeError), match="Expected pd.DataFrame"):
        DataFrameModel(df=[1, 2, 3])


def test_numpy_array_model_valid():
    """Test NumpyArrayModel with valid numpy array."""
    arr = np.array([1, 2, 3, 4, 5])
    model = NumpyArrayModel(array=arr)
    assert isinstance(model.array, np.ndarray)
    np.testing.assert_array_equal(model.array, arr)


def test_numpy_array_model_invalid():
    """Test NumpyArrayModel with invalid input (not a numpy array)."""
    with pytest.raises((ValidationError, TypeError), match="Expected numpy.ndarray"):
        NumpyArrayModel(array=[1, 2, 3])
