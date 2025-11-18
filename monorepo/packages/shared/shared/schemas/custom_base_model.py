from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        # json_serializers는 v2에서 다르게 처리
    )
