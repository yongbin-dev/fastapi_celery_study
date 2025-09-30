# tests/conftest.py
"""
pytest 설정 및 공통 fixture들
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# 테스트용 in-memory SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 데이터베이스 세션"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """테스트 클라이언트"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """데이터베이스 세션 fixture"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# 테스트 데이터 fixtures
@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers():
    """인증 헤더 (인증 시스템 구현 후 사용)"""
    return {"Authorization": "Bearer test-token"}


# 스트레스 테스트용 pytest 옵션과 fixture
def pytest_addoption(parser):
    """pytest 명령행 옵션 추가"""
    parser.addoption(
        "--num-chains",
        action="store",
        default=None,
        type=int,
        help="스트레스 테스트에서 실행할 체인 개수",
    )


@pytest.fixture
def num_chains(request):
    """체인 개수를 결정하는 fixture (우선순위: 명령행 > 환경변수 > 기본값)"""
    # 1. 명령행 옵션이 있으면 우선 사용
    if request.config.getoption("--num-chains"):
        return request.config.getoption("--num-chains")

    # 2. 환경변수 확인
    if os.getenv("TEST_NUM_CHAINS"):
        return int(os.getenv("TEST_NUM_CHAINS"))

    # 3. 기본값
    return 100
