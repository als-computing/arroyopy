from pydantic import BaseModel


class Message(BaseModel):
    pass


class Start(Message):
    pass


class Stop(Message):
    pass


class Event(Message):
    pass
