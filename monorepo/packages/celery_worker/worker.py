#!/usr/bin/env python3
# worker.py

"""
Celery 워커 시작 스크립트

환경변수(.env)로 worker 옵션을 제어합니다:
- CELERY_WORKER_POOL: solo, prefork, gevent, threads
- CELERY_WORKER_CONCURRENCY: 동시 실행 태스크 수
- CELERY_WORKER_PREFETCH_MULTIPLIER: prefetch 배수
- CELERY_WORKER_MAX_TASKS_PER_CHILD: worker 재시작 전 최대 태스크
- CELERY_WORKER_LOGLEVEL: 로그 레벨

사용법:
    python worker.py
"""

import os
import subprocess
import sys

if __name__ == "__main__":
    # 현재 디렉토리를 Python 경로에 추가
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Settings 로드
    from shared.config import settings
    from shared.core.logging import get_logger

    logger = get_logger(__name__)

    # Celery 워커 기본 명령어
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "celery_app",
        "worker",
    ]

    # Pool 설정
    pool = settings.CELERY_WORKER_POOL
    cmd.append(f"--pool={pool}")
    logger.info(f"🔧 Celery Worker Pool: {pool}")

    # Concurrency 설정 (solo일 때는 무시됨)
    if pool != "solo":
        concurrency = settings.CELERY_WORKER_CONCURRENCY
        cmd.append(f"--concurrency={concurrency}")
        logger.info(f"🔧 Celery Worker Concurrency: {concurrency}")

    # Prefetch Multiplier 설정
    prefetch = settings.CELERY_WORKER_PREFETCH_MULTIPLIER
    cmd.append(f"--prefetch-multiplier={prefetch}")

    # Max Tasks Per Child 설정
    max_tasks = settings.CELERY_WORKER_MAX_TASKS_PER_CHILD
    cmd.append(f"--max-tasks-per-child={max_tasks}")

    # Log Level 설정
    loglevel = settings.CELERY_WORKER_LOGLEVEL.lower()
    cmd.append(f"--loglevel={loglevel}")
    logger.info(f"🔧 Celery Worker Loglevel: {loglevel}")

    # 명령어 출력
    logger.info(f"📡 Starting Celery Worker: {' '.join(cmd)}")

    # Celery 워커 시작
    subprocess.run(cmd)
