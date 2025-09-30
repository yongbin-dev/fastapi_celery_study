# tests/conftest.py

import os

import pytest


def pytest_addoption(parser):
    """pytest 커맨드라인 옵션 추가"""
    parser.addoption(
        "--num-chains",
        action="store",
        default=100,
        type=int,
        help="동시에 실행할 체인 개수 (기본값: 100)",
    )


@pytest.fixture
def num_chains(request):
    """num_chains fixture - 커맨드라인 또는 환경변수에서 가져옴"""
    # 1. 커맨드라인 옵션 우선
    cmd_value = request.config.getoption("--num-chains")
    # 2. 환경변수
    env_value = os.environ.get("TEST_NUM_CHAINS")

    if env_value:
        return int(env_value)
    return cmd_value