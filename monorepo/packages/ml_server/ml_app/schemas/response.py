# app/domains/ocr/schemas/response.py

from pydantic import BaseModel, ConfigDict, Field
from shared.schemas.enums import PipelineStatus


class TestResultDTO(BaseModel):

    task_id: str  =Field(default="")
    status: PipelineStatus  = Field(default=PipelineStatus.PENDING)
    result: str  =Field(default="")

    model_config = ConfigDict(from_attributes=True)
