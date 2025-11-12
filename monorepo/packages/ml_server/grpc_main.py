"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import uvicorn
from shared.config import settings

if __name__ == "__grpc_main__":
    import uvicorn

    # uvicorn.run에서 reload=True 옵션을 사용하면
    # FastAPI의 lifespan 이벤트가 정상적으로 동작하지 않을 수 있습니다.
    # 대신 uvicorn CLI에서 --reload 옵션을 사용하는 것을 권장합니다.
    uvicorn.run(
        "ml_app.main:app",
        host=settings.HOST,
        port=settings.ML_SERVER_PORT,
        reload=False,
    )
