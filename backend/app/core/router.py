import os
import pkgutil
import traceback
from importlib import import_module

from fastapi import APIRouter

import app.domains
from app.core.logging import get_logger

logger = get_logger(__name__)


api_router = APIRouter()

# 1. 환경 변수에서 현재 도메인 가져오기
current_domain = os.getenv("DOMAIN", "base")
allowed_domains = {"base", current_domain}
logger.info(
    f"🚀 Current domain context: {current_domain}. Allowed domains: {allowed_domains}"
)


# 2. 도메인 컨트롤러 자동 검색 및 등록 (조건부 로드)
for _, domain_name, _ in pkgutil.iter_modules(app.domains.__path__):
    if domain_name in allowed_domains:
        try:
            controller_module = import_module(
                f"app.domains.{domain_name}.controllers.{domain_name}_controller"
            )

            api_router.include_router(
                controller_module.router,
                tags=[domain_name.upper()],
            )
            logger.info(f"✅ Loaded domain controller: {domain_name}")
        except (ImportError, AttributeError) as e:
            logger.error(f"에러 발생: {traceback.format_exc()}")
            logger.warning(f"⚠️ No controller found for domain: {domain_name} - {e}")
    else:
        logger.debug(
            f"⏭️ Skipping domain controller: {domain_name} (not in allowed list)"
        )


# 3. 오케스트레이션 컨트롤러 등록 (pipeline_controller) - 모든 도메인에 공통으로 필요 시
try:
    from app.orchestration.controllers.pipeline_controller import (
        router as pipeline_router,
    )

    api_router.include_router(pipeline_router, tags=["Orchestration"])
    logger.info("✅ Loaded orchestration controller: pipeline")
except (ImportError, AttributeError) as e:
    logger.warning(f"⚠️ Failed to load pipeline controller: {e}")
