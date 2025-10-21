"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

# 프로젝트 루트를 sys.path에 추가
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.core.auto_router import setup_auto_routers
from shared.core.logging import get_logger
from shared.middleware.request_middleware import RequestLogMiddleware
from shared.middleware.response_middleware import ResponseLogMiddleware

logger = get_logger(__name__)

app = FastAPI(
    title="ML Model Server",
    version="1.0.0",
    description="AI/ML 모델 추론 서버 - OCR, LLM 등",
)


# 라우터 설정
def setup_routers():
    """라우터 설정 - 자동 스캔 및 등록"""
    import pathlib

    current_dir = pathlib.Path(__file__).parent
    domains_path = str(current_dir / "domains")

    app.add_middleware(ResponseLogMiddleware)
    app.add_middleware(RequestLogMiddleware)
    # CORS 미들웨어 (가장 먼저 실행되어야 함)
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✅ 미들웨어 설정 완료")

    auto_router = setup_auto_routers(
        app=app,
        domains_path=domains_path,
        exclude_domains=[],
        global_prefix="/api/model",
    )

    # 등록된 router 정보 로깅
    registered = auto_router.get_registered_routers()
    logger.info(f"✅ 라우터 설정 완료 - 등록된 routers: {len(registered)}개")
    for router_info in registered:
        logger.info(
            f"  - {router_info['module']} "
            f"(prefix: {router_info['prefix']}, "
            f"tags: {router_info['tags']})"
        )


setup_routers()


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
