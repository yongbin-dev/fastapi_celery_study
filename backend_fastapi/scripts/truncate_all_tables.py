#!/usr/bin/env python3
"""
DB 테이블 전체 데이터 truncate 스크립트

사용법:
    python scripts/truncate_all_tables.py [옵션]

옵션:
    --confirm      : 확인 프롬프트 없이 실행
    --exclude TEXT : 제외할 테이블명 (쉼표로 구분, 예: --exclude users,logs)
    --dry-run      : 실제 실행하지 않고 삭제될 테이블만 출력
    --test-db      : 테스트 데이터베이스 사용 (TEST_DATABASE_URL)
    --stats        : 테이블별 레코드 수만 출력
    --help         : 도움말 출력

주의사항:
- 이 스크립트는 모든 테이블의 데이터를 삭제합니다.
- 외래키 제약 조건을 일시적으로 비활성화합니다.
- 개발 환경에서만 사용하세요.
"""

import asyncio
import sys
import argparse
from typing import List, Set
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db_manager
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TableTruncator:
    """테이블 데이터 truncate를 담당하는 클래스"""

    def __init__(self, exclude_tables: Set[str] = None, use_test_db: bool = False):
        # 데이터베이스 URL 설정
        if use_test_db:
            # 테스트 DB용 설정으로 데이터베이스 매니저 설정 오버라이드
            original_db_url = settings.DATABASE_URL
            settings.DATABASE_URL = settings.TEST_DATABASE_URL
            self.db_manager = get_db_manager()
            settings.DATABASE_URL = original_db_url  # 원복
            self.db_url = settings.TEST_DATABASE_URL
        else:
            self.db_manager = get_db_manager()
            self.db_url = settings.DATABASE_URL

        self.exclude_tables = exclude_tables or set()
        # 기본적으로 제외할 시스템 테이블들
        self.exclude_tables.update({
            'alembic_version',  # 마이그레이션 버전 정보
            'information_schema',
            'pg_catalog',
            'pg_stat_statements'
        })

    async def get_all_tables(self) -> List[str]:
        """데이터베이스의 모든 테이블 목록 조회"""
        try:
            async with self.db_manager.async_engine.begin() as conn:
                # PostgreSQL에서 사용자 테이블 목록 조회
                query = text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                result = await conn.execute(query)
                tables = [row[0] for row in result.fetchall()]

                # 제외할 테이블 필터링
                filtered_tables = [
                    table for table in tables
                    if table not in self.exclude_tables
                ]

                return filtered_tables
        except Exception as e:
            logger.error(f"테이블 목록 조회 실패: {e}")
            raise

    async def truncate_all_tables(self, dry_run: bool = False) -> bool:
        """모든 테이블의 데이터를 truncate"""
        try:
            tables = await self.get_all_tables()

            if not tables:
                print("📝 truncate할 테이블이 없습니다.")
                return True

            if dry_run:
                print("🔍 DRY RUN 모드: 다음 테이블들이 truncate됩니다:")
                for table in tables:
                    print(f"  - {table}")
                return True

            print(f"🗑️  {len(tables)}개 테이블의 데이터를 삭제합니다...")

            async with self.db_manager.async_engine.begin() as conn:
                # 외래키 제약 조건 일시 비활성화
                await conn.execute(text("SET session_replication_role = replica;"))

                try:
                    # 각 테이블 truncate
                    for table in tables:
                        print(f"  🧹 {table} 테이블 정리 중...")
                        await conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                        logger.info(f"테이블 {table} truncate 완료")

                    print("✅ 모든 테이블 데이터 삭제 완료!")
                    return True

                finally:
                    # 외래키 제약 조건 다시 활성화
                    await conn.execute(text("SET session_replication_role = DEFAULT;"))

        except SQLAlchemyError as e:
            logger.error(f"데이터베이스 오류: {e}")
            print(f"❌ 데이터베이스 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            print(f"❌ 예상치 못한 오류: {e}")
            return False

    async def get_table_stats(self) -> dict:
        """각 테이블의 레코드 수 조회"""
        try:
            tables = await self.get_all_tables()
            stats = {}

            async with self.db_manager.async_engine.begin() as conn:
                for table in tables:
                    try:
                        result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        stats[table] = count
                    except Exception as e:
                        logger.warning(f"테이블 {table}의 레코드 수 조회 실패: {e}")
                        stats[table] = "ERROR"

            return stats
        except Exception as e:
            logger.error(f"테이블 통계 조회 실패: {e}")
            return {}


def parse_exclude_tables(exclude_str: str) -> Set[str]:
    """제외할 테이블 문자열을 파싱"""
    if not exclude_str:
        return set()
    return {table.strip() for table in exclude_str.split(',') if table.strip()}


async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="DB 테이블 전체 데이터 truncate 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/truncate_all_tables.py --dry-run
  python scripts/truncate_all_tables.py --confirm
  python scripts/truncate_all_tables.py --exclude users,logs --confirm
        """
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='확인 프롬프트 없이 바로 실행'
    )

    parser.add_argument(
        '--exclude',
        type=str,
        default='',
        help='제외할 테이블명 (쉼표로 구분)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 실행하지 않고 삭제될 테이블만 출력'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='각 테이블의 레코드 수만 출력'
    )

    parser.add_argument(
        '--test-db',
        action='store_true',
        help='테스트 데이터베이스 사용 (TEST_DATABASE_URL)'
    )

    args = parser.parse_args()

    # 환경 확인
    if settings.environment == "production":
        print("❌ 프로덕션 환경에서는 이 스크립트를 실행할 수 없습니다!")
        sys.exit(1)

    # 데이터베이스 선택
    use_test_db = args.test_db

    # 대화형으로 데이터베이스 선택 (옵션이 제공되지 않은 경우)
    if not use_test_db and not args.confirm and not args.dry_run:
        print("\n📋 사용할 데이터베이스를 선택하세요:")
        print("  1. 기본 데이터베이스 (DATABASE_URL)")
        print("  2. 테스트 데이터베이스 (TEST_DATABASE_URL)")

        while True:
            try:
                choice = input("\n선택 (1 또는 2): ").strip()
                if choice == "1":
                    use_test_db = False
                    break
                elif choice == "2":
                    use_test_db = True
                    break
                else:
                    print("❌ 1 또는 2를 입력해주세요.")
            except KeyboardInterrupt:
                print("\n❌ 작업이 취소되었습니다.")
                sys.exit(1)

    # 선택된 데이터베이스 정보 출력
    db_url = settings.TEST_DATABASE_URL if use_test_db else settings.DATABASE_URL
    db_type = "테스트" if use_test_db else "기본"

    print(f"🔧 환경: {settings.environment}")
    print(f"🎯 DB 타입: {db_type} 데이터베이스")
    print(f"🔗 DB: {db_url.split('@')[-1]}")  # 비밀번호 제외하고 출력

    # 제외할 테이블 파싱
    exclude_tables = parse_exclude_tables(args.exclude)
    if exclude_tables:
        print(f"🚫 제외할 테이블: {', '.join(exclude_tables)}")

    try:
        truncator = TableTruncator(exclude_tables, use_test_db)

        # 통계만 출력하는 경우
        if args.stats:
            print("\n📊 테이블별 레코드 수:")
            stats = await truncator.get_table_stats()
            if stats:
                total_records = 0
                for table, count in stats.items():
                    if isinstance(count, int):
                        total_records += count
                        print(f"  {table}: {count:,}개")
                    else:
                        print(f"  {table}: {count}")
                print(f"\n총 레코드 수: {total_records:,}개")
            else:
                print("  통계를 가져올 수 없습니다.")
            return

        # dry-run이 아닌 경우 확인 프롬프트
        if not args.dry_run and not args.confirm:
            # 현재 데이터 상태 출력
            print("\n📊 현재 테이블 상태:")
            stats = await truncator.get_table_stats()
            if stats:
                total_records = 0
                for table, count in stats.items():
                    if isinstance(count, int) and count > 0:
                        total_records += count
                        print(f"  {table}: {count:,}개")

                if total_records == 0:
                    print("  모든 테이블이 이미 비어있습니다.")
                    return

                print(f"\n⚠️  총 {total_records:,}개의 레코드가 삭제됩니다!")

            response = input("\n정말로 모든 테이블 데이터를 삭제하시겠습니까? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ 작업이 취소되었습니다.")
                return

        # 실행
        success = await truncator.truncate_all_tables(dry_run=args.dry_run)

        if success and not args.dry_run:
            print("\n📊 작업 완료 후 상태:")
            stats = await truncator.get_table_stats()
            total_remaining = sum(count for count in stats.values() if isinstance(count, int))
            print(f"  총 남은 레코드: {total_remaining}개")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"스크립트 실행 실패: {e}")
        print(f"❌ 스크립트 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())