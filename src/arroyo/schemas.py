import numpy
import pandas
from pydantic import BaseModel, field_validator


class Message:
    """ "
    Base class for messages. Is not a pydantic model
    in case implementations choose not to use pydantic
    as a validation and (de)serialization system but still
    want to indicate that they pass arroyo Messages.
    """

    pass


class PydanticMessage(Message, BaseModel):
    pass


class Start(PydanticMessage):
    pass


class Stop(PydanticMessage):
    pass


class Event(PydanticMessage):
    pass


class DataFrameModel(BaseModel):
    """
    A Pydantic model for validating pd.DataFrame objects.
    Does not parse array, merely validates that is a pd.DataFrame
    """

    df: pandas.DataFrame

    @field_validator("df", mode="before")
    def validate_is_numpy_array(cls, v):
        if not isinstance(v, pandas.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(v)} instead.")
        return v  # Do not modify or parse the array

    class Config:
        arbitrary_types_allowed = True  # Allow numpy.ndarray type


class NumpyArrayModel(BaseModel):
    """
    A Pydantic model for validating numpy.ndarray objects.
    Does not parse array, merely validates that is a np.ndarray
    """

    array: numpy.ndarray

    @field_validator("array", mode="before")
    def validate_is_numpy_array(cls, v):
        if not isinstance(v, numpy.ndarray):
            raise TypeError(f"Expected numpy.ndarray, got {type(v)} instead.")
        return v  # Do not modify or parse the array

    class Config:
        arbitrary_types_allowed = True  # Allow numpy.ndarray type
