from typing import ClassVar as _ClassVar
from typing import Iterable as _Iterable
from typing import Mapping as _Mapping
from typing import Optional as _Optional

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATUS_UNKNOWN: _ClassVar[Status]
    STATUS_SUCCESS: _ClassVar[Status]
    STATUS_FAILURE: _ClassVar[Status]
    STATUS_PENDING: _ClassVar[Status]
    STATUS_IN_PROGRESS: _ClassVar[Status]

STATUS_UNKNOWN: Status
STATUS_SUCCESS: Status
STATUS_FAILURE: Status
STATUS_PENDING: Status
STATUS_IN_PROGRESS: Status

class Timestamp(_message.Message):
    __slots__: tuple[str, ...] = ("seconds", "nanos")
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    NANOS_FIELD_NUMBER: _ClassVar[int]
    seconds: int
    nanos: int
    def __init__(
        self, seconds: _Optional[int] = ..., nanos: _Optional[int] = ...
    ) -> None: ...

class BoundingBox(_message.Message):
    __slots__: tuple[str, ...] = ("coordinates",)
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    coordinates: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, coordinates: _Optional[_Iterable[float]] = ...) -> None: ...

class Metadata(_message.Message):
    __slots__: tuple[str, ...] = ("data",)
    class DataEntry(_message.Message):
        __slots__: tuple[str, ...] = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _containers.ScalarMap[str, str]
    def __init__(self, data: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ErrorInfo(_message.Message):
    __slots__: tuple[str, ...] = ("code", "message", "details")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    code: str
    message: str
    details: str
    def __init__(
        self,
        code: _Optional[str] = ...,
        message: _Optional[str] = ...,
        details: _Optional[str] = ...,
    ) -> None: ...
