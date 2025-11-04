import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class OCRRequest(_message.Message):
    __slots__ = ("public_image_path", "private_image_path", "language", "confidence_threshold", "use_angle_cls", "options")
    PUBLIC_IMAGE_PATH_FIELD_NUMBER: _ClassVar[int]
    PRIVATE_IMAGE_PATH_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    USE_ANGLE_CLS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    public_image_path: str
    private_image_path: str
    language: str
    confidence_threshold: float
    use_angle_cls: bool
    options: _common_pb2.Metadata
    def __init__(self, public_image_path: _Optional[str] = ..., private_image_path: _Optional[str] = ..., language: _Optional[str] = ..., confidence_threshold: _Optional[float] = ..., use_angle_cls: bool = ..., options: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ...) -> None: ...

class OCRResponse(_message.Message):
    __slots__ = ("status", "text", "overall_confidence", "text_boxes", "metadata", "error")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    OVERALL_CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    TEXT_BOXES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    status: _common_pb2.Status
    text: str
    overall_confidence: float
    text_boxes: _containers.RepeatedCompositeFieldContainer[TextBox]
    metadata: _common_pb2.Metadata
    error: _common_pb2.ErrorInfo
    def __init__(self, status: _Optional[_Union[_common_pb2.Status, str]] = ..., text: _Optional[str] = ..., overall_confidence: _Optional[float] = ..., text_boxes: _Optional[_Iterable[_Union[TextBox, _Mapping]]] = ..., metadata: _Optional[_Union[_common_pb2.Metadata, _Mapping]] = ..., error: _Optional[_Union[_common_pb2.ErrorInfo, _Mapping]] = ...) -> None: ...

class TextBox(_message.Message):
    __slots__ = ("text", "confidence", "bbox")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    BBOX_FIELD_NUMBER: _ClassVar[int]
    text: str
    confidence: float
    bbox: _common_pb2.BoundingBox
    def __init__(self, text: _Optional[str] = ..., confidence: _Optional[float] = ..., bbox: _Optional[_Union[_common_pb2.BoundingBox, _Mapping]] = ...) -> None: ...

class OCRBatchRequest(_message.Message):
    __slots__ = ("image_paths", "language", "confidence_threshold", "use_angle_cls")
    IMAGE_PATHS_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    USE_ANGLE_CLS_FIELD_NUMBER: _ClassVar[int]
    image_paths: _containers.RepeatedCompositeFieldContainer[ImagePath]
    language: str
    confidence_threshold: float
    use_angle_cls: bool
    def __init__(self, image_paths: _Optional[_Iterable[_Union[ImagePath, _Mapping]]] = ..., language: _Optional[str] = ..., confidence_threshold: _Optional[float] = ..., use_angle_cls: bool = ...) -> None: ...

class ImagePath(_message.Message):
    __slots__ = ("public_path", "private_path")
    PUBLIC_PATH_FIELD_NUMBER: _ClassVar[int]
    PRIVATE_PATH_FIELD_NUMBER: _ClassVar[int]
    public_path: str
    private_path: str
    def __init__(self, public_path: _Optional[str] = ..., private_path: _Optional[str] = ...) -> None: ...

class OCRBatchProgress(_message.Message):
    __slots__ = ("batch_id", "total_images", "processed_images", "current_result", "progress_percentage")
    BATCH_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_IMAGES_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_IMAGES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_RESULT_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    batch_id: str
    total_images: int
    processed_images: int
    current_result: OCRResponse
    progress_percentage: float
    def __init__(self, batch_id: _Optional[str] = ..., total_images: _Optional[int] = ..., processed_images: _Optional[int] = ..., current_result: _Optional[_Union[OCRResponse, _Mapping]] = ..., progress_percentage: _Optional[float] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ("service_name",)
    SERVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    service_name: str
    def __init__(self, service_name: _Optional[str] = ...) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "engine_type", "model_loaded", "version")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ENGINE_TYPE_FIELD_NUMBER: _ClassVar[int]
    MODEL_LOADED_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    status: _common_pb2.Status
    engine_type: str
    model_loaded: bool
    version: str
    def __init__(self, status: _Optional[_Union[_common_pb2.Status, str]] = ..., engine_type: _Optional[str] = ..., model_loaded: bool = ..., version: _Optional[str] = ...) -> None: ...
