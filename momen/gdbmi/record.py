from enum import Enum
from dataclasses import dataclass, field
from typing import Union


class RecordType(Enum):
    RESULT = "result"
    STREAM = "stream"
    ASYNC = "async"
    PROMPT = "prompt"


PayloadValue = Union[str, "Payload", list["PayloadValue"]]
Payload = dict[str, PayloadValue]


@dataclass
class RecordBase:
    type: RecordType = field(init=False)


@dataclass
class ResultRecord(RecordBase):
    result_class: str
    payload: Payload

    def __post_init__(self):
        self.type = RecordType.RESULT

    def is_error(self) -> bool:
        return self.result_class == "error"


@dataclass
class AsyncRecord(RecordBase):
    async_class: str
    payload: Payload

    def __post_init__(self):
        self.type = RecordType.ASYNC


class StreamType(Enum):
    OUTPUT = "~"
    INPUT = "@"
    ERROR = "&"


@dataclass
class StreamRecord(RecordBase):
    stream_type: StreamType
    payload: str

    def __post_init__(self):
        self.type = RecordType.STREAM


@dataclass
class PromptRecord(RecordBase):
    def __post_init__(self):
        self.type = RecordType.PROMPT


Record = ResultRecord | AsyncRecord | StreamRecord | PromptRecord
