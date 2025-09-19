from pydantic import BaseModel


class PredictRequest(BaseModel):
    prompt: str
    server: str = "server1"
    model: str = "qwen2"  # 기본값
    stream: bool = False


class PredictResponse(BaseModel):
    response: str
