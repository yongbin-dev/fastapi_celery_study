#!/usr/bin/env python3
# worker.py

"""
Celery 워커 시작 스크립트

사용법:
    python worker.py

또는 직접 celery 명령:
    python -m celery -A celery_app worker --loglevel=info
"""

import os
import subprocess
import sys

if __name__ == "__main__":
    # 현재 디렉토리를 Python 경로에 추가
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Celery 워커 시작
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "celery_app",
        "worker",
        "--loglevel=info",
    ]

    subprocess.run(cmd)
