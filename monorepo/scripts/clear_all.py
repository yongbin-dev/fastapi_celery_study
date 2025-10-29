#!/usr/bin/env python3
"""
Supabase Storage와 PostgreSQL DB 전체 데이터를 삭제하는 스크립트

실행 방법:
    python scripts/clear_all.py

주의사항:
    - 이 스크립트는 모든 데이터를 삭제합니다
    - 프로덕션 환경에서는 절대 실행하지 마세요
    - 개발 환경에서만 사용하세요
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.config import settings  # noqa: E402
from shared.core.database import get_db_manager  # noqa: E402
from shared.models import (  # noqa: E402
    BatchExecution,
    ChainExecution,
    OCRExecution,
    OCRTextBox,
    TaskLog,
)


class DataCleaner:
    """데이터 정리 클래스"""

    def __init__(self):
        # SERVICE_ROLE_KEY 사용 (관리자 권한 필요)
        self.db_manager = get_db_manager()

    async def clear_database(self) -> None:
        """PostgreSQL 데이터베이스의 모든 테이블 데이터 삭제"""
        print("\n🗑️  Database 정리 중...")

        # 삭제 순서 (외래 키 제약 조건 고려)
        tables_to_clear = [
            ("ocr_text_boxes", OCRTextBox.__tablename__),
            ("ocr_executions", OCRExecution.__tablename__),
            ("task_logs", TaskLog.__tablename__),
            ("chain_executions", ChainExecution.__tablename__),
            ("batch_executions", BatchExecution.__tablename__),
        ]

        try:
            async with self.db_manager.async_engine.begin() as conn:
                total_deleted = 0

                for table_name, table in tables_to_clear:
                    try:
                        # TRUNCATE는 더 빠르지만 외래 키 제약 조건 때문에 DELETE 사용
                        result = await conn.execute(
                            text(f"DELETE FROM {table}")
                        )
                        deleted_count = result.rowcount or 0
                        total_deleted += deleted_count

                        if deleted_count > 0:
                            print(f"   ✅ {table_name}: {deleted_count}개 행 삭제")
                        else:
                            print(f"   ℹ️  {table_name}: 삭제할 데이터 없음")

                    except Exception as e:
                        print(f"   ⚠️  {table_name} 삭제 실패: {str(e)}")
                        continue

                print(f"\n   ✅ Database 정리 완료: 총 {total_deleted}개 행 삭제")

        except Exception as e:
            print(f"   ❌ Database 정리 실패: {str(e)}")
            raise

    async def clear_all(self, debug: bool = False) -> None:
        """모든 데이터 삭제 (Storage + Database)"""
        print("=" * 60)
        print("🧹 데이터 전체 삭제 시작")
        if debug:
            print("🐛 디버그 모드: ON")
        print("=" * 60)

        try:
            # Storage 정리
            # self.clear_supabase_storage(debug=debug)

            # Database 정리
            await self.clear_database()

            print("\n" + "=" * 60)
            print("✅ 모든 데이터 삭제 완료!")
            print("=" * 60)

        except Exception as e:
            print("\n" + "=" * 60)
            print(f"❌ 데이터 삭제 중 오류 발생: {str(e)}")
            print("=" * 60)
            sys.exit(1)


async def main():
    """메인 실행 함수"""

    # 디버그 모드 확인 (환경 변수 또는 인자)
    import os
    debug = os.getenv("DEBUG_MODE", "").lower() in ("true", "1", "yes")
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        debug = True

    # 환경 확인
    if settings.ENVIRONMENT != "development":
        print("❌ 이 스크립트는 개발 환경에서만 실행할 수 있습니다")
        print(f"   현재 환경: {settings.ENVIRONMENT}")
        sys.exit(1)

    # 사용자 확인
    print("\n⚠️  경고: 이 작업은 모든 데이터를 삭제합니다!")
    print(f"   - Supabase Storage (버킷: {settings.SUPABASE_STORAGE_BUCKET})")
    print("   - PostgreSQL Database (모든 테이블)")
    print(f"   - 환경: {settings.ENVIRONMENT}")
    if debug:
        print("   - 디버그 모드: 활성화 (상세 로그 출력)")

    response = input("\n계속하시겠습니까? (yes/no): ").strip().lower()

    if response != "yes":
        print("❌ 작업이 취소되었습니다")
        sys.exit(0)

    # 데이터 삭제 실행
    cleaner = DataCleaner()
    await cleaner.clear_all(debug=debug)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {str(e)}")
        sys.exit(1)
