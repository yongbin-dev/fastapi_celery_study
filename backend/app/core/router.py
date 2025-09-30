import pkgutil
from importlib import import_module

from fastapi import APIRouter

import app.domains
from app.core.logging import get_logger

logger = get_logger(__name__)


api_router = APIRouter()

# 1. 도메인 컨트롤러 자동 검색 및 등록
for _, domain_name, _ in pkgutil.iter_modules(app.domains.__path__):
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
        logger.warning(f"⚠️ No controller found for domain: {domain_name} - {e}")

# 2. 오케스트레이션 컨트롤러 등록 (pipeline_controller)
try:
    from app.orchestration.controllers.pipeline_controller import (
        router as pipeline_router,
    )

    api_router.include_router(pipeline_router, tags=["Orchestration"])
    logger.info("✅ Loaded orchestration controller: pipeline")
except (ImportError, AttributeError) as e:
    logger.warning(f"⚠️ Failed to load pipeline controller: {e}")
