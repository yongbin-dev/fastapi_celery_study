# app/core/auto_router.py
"""
자동 라우터 등록 유틸리티

domains 디렉토리 내의 모든 controller를 자동으로 스캔하고 등록합니다.
"""

import importlib
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, FastAPI

from shared.core.logging import get_logger

logger = get_logger(__name__)


class AutoRouter:
    """도메인 컨트롤러 자동 등록 관리자"""

    def __init__(
        self,
        app: FastAPI,
        domains_path: str = "app/domains",
        controller_suffix: str = "_controller.py",
        exclude_domains: Optional[list[str]] = None,
        global_prefix: str = "",
    ):
        """
        Args:
            app: FastAPI 애플리케이션 인스턴스
            domains_path: 도메인 디렉토리 경로
            controller_suffix: 컨트롤러 파일 접미사
            exclude_domains: 제외할 도메인 목록
            global_prefix: 모든 라우터에 적용할 전역 prefix (예: "/api/v1")
        """
        self.app = app
        self.domains_path = Path(domains_path)
        self.controller_suffix = controller_suffix
        self.exclude_domains = exclude_domains or []
        self.global_prefix = global_prefix
        self.registered_routers: list[dict[str, Any]] = []

    def discover_controllers(self) -> list[Path]:
        """
        domains 디렉토리에서 모든 controller 파일을 찾습니다.

        Returns:
            controller 파일 경로 리스트
        """
        controller_files = []

        # domains 디렉토리 존재 확인
        if not self.domains_path.exists():
            logger.warning(
                f"domains 디렉토리를 찾을 수 없습니다: {self.domains_path}"
            )
            return controller_files

        # domains 디렉토리 내의 모든 도메인 탐색
        for domain_dir in self.domains_path.iterdir():
            if not domain_dir.is_dir():
                continue

            # 제외된 도메인 스킵
            if domain_dir.name in self.exclude_domains or domain_dir.name.startswith(
                ("_", ".")
            ):
                continue

            # controllers 디렉토리 확인
            controllers_dir = domain_dir / "controllers"
            if not controllers_dir.exists() or not controllers_dir.is_dir():
                logger.debug(f"도메인 '{domain_dir.name}'에 controllers 디렉토리 없음")
                continue

            # controller 파일 찾기
            for controller_file in controllers_dir.glob(f"*{self.controller_suffix}"):
                if controller_file.name.startswith("_"):
                    continue
                controller_files.append(controller_file)
                logger.debug(f"Controller 발견: {controller_file}")

        return controller_files

    def import_router_from_file(self, file_path: Path) -> Optional[APIRouter]:
        """
        파일에서 router 객체를 동적으로 import합니다.

        Args:
            file_path: controller 파일 경로

        Returns:
            APIRouter 인스턴스 또는 None
        """
        try:
            # 파일 경로를 모듈 경로로 변환
            # domains_path의 2단계 부모를 기준으로 상대 경로 계산
            # 예: file_path = /path/to/ml_server/app/domains/ocr/controllers/ocr_controller.py
            #     domains_path = /path/to/ml_server/app/domains
            #     base_path = /path/to/ml_server (domains_path.parent.parent)
            #  -> app.domains.ocr.controllers.ocr_controller
            base_path = self.domains_path.parent.parent
            relative_path = file_path.relative_to(base_path)
            module_path = str(relative_path).replace("/", ".").replace(".py", "")

            # 모듈 동적 import
            module = importlib.import_module(module_path)

            # router 객체 찾기
            if hasattr(module, "router"):
                router = getattr(module, "router")
                if isinstance(router, APIRouter):
                    logger.debug(f"Router 로드 성공: {module_path}")
                    return router
                else:
                    logger.warning(
                        f"'{module_path}'의 router는 APIRouter 타입이 아닙니다"
                    )
            else:
                logger.warning(f"'{module_path}'에 router 객체가 없습니다")

        except Exception as e:
            logger.error(f"Router import 실패 ({file_path}): {e}")

        return None

    def register_router(
        self,
        router: APIRouter,
        module_path: str,
        prefix: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """
        router를 FastAPI 앱에 등록합니다.

        Args:
            router: 등록할 APIRouter 인스턴스
            module_path: 모듈 경로 (로깅용)
            prefix: 커스텀 prefix (None이면 router의 기본 prefix 사용)
            tags: 추가 태그

        Returns:
            등록 성공 여부
        """
        try:

            # global_prefix와 router_prefix를 결합
            final_prefix = self.global_prefix

            router_tags_raw = tags or getattr(router, "tags", [])
            # FastAPI expects Optional[List[str | Enum]]
            router_tags = (
                list(router_tags_raw) if router_tags_raw else None
            )

            self.app.include_router(
                router, prefix=final_prefix, tags=router_tags # type: ignore
            )

            self.registered_routers.append(
                {
                    "module": module_path,
                    "prefix": final_prefix,
                    "tags": router_tags or [],
                }
            )

            logger.info(
                f"✅ Router 등록: {module_path} "
                f"(prefix: {final_prefix}, tags: {router_tags})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Router 등록 실패 ({module_path}): {e}")
            return False

    def auto_register_all(self) -> int:
        """
        모든 controller를 자동으로 검색하고 등록합니다.

        Returns:
            등록된 router 수
        """
        logger.info("🔍 Controller 자동 등록 시작...")

        controller_files = self.discover_controllers()
        logger.info(f"발견된 controller 파일: {len(controller_files)}개")

        registered_count = 0

        for file_path in controller_files:
            # Router import
            router = self.import_router_from_file(file_path)
            if router is None:
                continue

            # 모듈 경로 생성 (로깅용)
            base_path = self.domains_path.parent.parent
            relative_path = file_path.relative_to(base_path)
            module_path = str(relative_path).replace("/", ".").replace(".py", "")

            # Router 등록
            if self.register_router(router, module_path):
                registered_count += 1

        logger.info(f"🎉 총 {registered_count}개의 router가 등록되었습니다")

        return registered_count

    def get_registered_routers(self) -> list[dict[str, Any]]:
        """등록된 router 정보를 반환합니다."""
        return self.registered_routers


def setup_auto_routers(
    app: FastAPI,
    domains_path: str = "app/domains",
    exclude_domains: Optional[list[str]] = None,
    global_prefix: str = "",
) -> AutoRouter:
    """
    자동 라우터 등록을 설정하고 실행합니다.

    Args:
        app: FastAPI 애플리케이션
        domains_path: domains 디렉토리 경로
        exclude_domains: 제외할 도메인 목록
        global_prefix: 모든 라우터에 적용할 전역 prefix (예: "/api/v1")

    Returns:
        AutoRouter 인스턴스

    Example:
        >>> app = FastAPI()
        >>> auto_router = setup_auto_routers(
        ...     app,
        ...     exclude_domains=["test", "deprecated"],
        ...     global_prefix="/api/v1"
        ... )
        >>> print(
        ...     f"등록된 routers: {len(auto_router.get_registered_routers())}"
        ... )
    """
    auto_router = AutoRouter(
        app=app,
        domains_path=domains_path,
        exclude_domains=exclude_domains,
        global_prefix=global_prefix,
    )

    auto_router.auto_register_all()

    return auto_router
