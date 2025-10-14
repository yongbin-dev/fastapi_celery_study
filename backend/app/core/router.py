import os
import pkgutil
from importlib import import_module

from fastapi import APIRouter

import app.domains
from app.core.logging import get_logger

logger = get_logger(__name__)


api_router = APIRouter()

# 1. 환경 변수에서 현재 도메인 가져오기
current_domain = os.getenv("DOMAIN", "base")


# 2. 도메인 컨트롤러 자동 검색 및 등록 (조건부 로드)
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
