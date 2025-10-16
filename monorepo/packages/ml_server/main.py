"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import settings

app = FastAPI(
    title="ML Model Server",
    version="1.0.0",
    description="AI/ML 모델 추론 서버 - OCR, LLM 등",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OCR 라우터 추가
from ml_server.ocr.server import app as ocr_app

app.mount("/ocr", ocr_app)


@app.get("/")
async def root():
    return {
        "service": "ML Model Server",
        "version": "1.0.0",
        "models": ["ocr"],
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ml_server"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENABLE_RELOAD,
    )
