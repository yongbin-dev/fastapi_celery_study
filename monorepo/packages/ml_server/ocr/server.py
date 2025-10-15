# model_servers/ocr_server/server.py
import sys

from fastapi import FastAPI, File, UploadFile

# 기존 앱 코드 재사용
sys.path.append('/app')
from .ocr_model import get_ocr_model

app = FastAPI(title="OCR Model Server", version="1.0.0")


@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    OCR 예측 엔드포인트

    Args:
        image: 이미지 파일

    Returns:
        OCR 결과 (text_boxes, full_text, status)
    """
    image_data = await image.read()

    # 기존 OCR 모델 사용
    model = get_ocr_model()
    result = model.predict(image_data, confidence_threshold=0.5)

    return result


@app.get("/health")
async def health():
    """헬스 체크"""
    model = get_ocr_model()
    return {
        "status": "healthy",
        "model_loaded": model.is_loaded
    }


@app.get("/metrics")
async def metrics():
    """메트릭 조회"""
    # 추후 GPU 메모리 사용량 등 추가 가능
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
