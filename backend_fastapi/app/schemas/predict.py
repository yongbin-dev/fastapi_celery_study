from pydantic import BaseModel

class PredictRequest(BaseModel):
    prompt: str
    model: str = "qwen2"  # 기본값
    stream: bool = False

class PredictResponse(BaseModel):
    success: bool
    response: str = None
    error: str = None