
"""
Celery 메소드 테스트 스크립트
다양한 Celery 기능들을 테스트할 수 있는 환경을 제공합니다.
"""

import time
import asyncio
from celery import Celery, group, chain, chord, signature
from celery.result import AsyncResult
from app.core.config import settings
from app.tasks import (
    example_task,
    simple_task, 
    ai_processing_task,
    send_email_task,
    long_running_task
)

# Celery 인스턴스 생성
celery_app = Celery(
    "study",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)


def test_basic_task():
    """기본 태스크 실행 테스트"""
    print("=== 기본 태스크 테스트 ===")
    
    # 동기식 실행
    result = simple_task.delay("Hello Celery!")
    print(f"Task ID: {result.id}")
    print(f"Task Result: {result.get(timeout=10)}")
    print()


def test_task_with_progress():
    """진행률 추적 태스크 테스트"""
    print("=== 진행률 추적 태스크 테스트 ===")
    
    result = example_task.delay("Progress Test", 5)
    print(f"Task ID: {result.id}")
    
    # 진행률 모니터링
    while not result.ready():
        task_result = AsyncResult(result.id)
        if task_result.state == 'PROGRESS':
            meta = task_result.info
            print(f"Progress: {meta['current']}/{meta['total']} - {meta['status']}")
        time.sleep(1)
    
    print(f"Final Result: {result.get()}")
    print()


def test_task_status():
    """태스크 상태 확인 테스트"""
    print("=== 태스크 상태 확인 테스트 ===")
    
    result = long_running_task.delay(5)
    print(f"Task ID: {result.id}")
    
    # 상태별 처리
    while True:
        status = result.status
        print(f"Current Status: {status}")
        
        if status == 'PENDING':
            print("Task is waiting to be processed")
        elif status == 'PROGRESS':
            print(f"Progress Info: {result.info}")
        elif status == 'SUCCESS':
            print(f"Task completed: {result.result}")
            break
        elif status == 'FAILURE':
            print(f"Task failed: {result.info}")
            break
            
        time.sleep(2)
    print()


def test_multiple_tasks():
    """여러 태스크 동시 실행 테스트"""
    print("=== 여러 태스크 동시 실행 테스트 ===")
    
    tasks = [
        simple_task.delay(f"Message {i}")
        for i in range(5)
    ]
    
    print(f"Started {len(tasks)} tasks")
    
    # 모든 태스크 완료 대기
    results = [task.get(timeout=30) for task in tasks]
    
    for i, result in enumerate(results):
        print(f"Task {i+1}: {result}")
    print()


def test_group_execution():
    """그룹 실행 테스트 - 여러 태스크 병렬 실행"""
    print("=== 그룹 실행 테스트 ===")
    
    # 그룹으로 여러 태스크 병렬 실행
    job = group([
        simple_task.s(f"Group Task {i}")
        for i in range(3)
    ])
    
    result = job.apply_async()
    print(f"Group ID: {result.id}")
    
    # 모든 결과 수집
    results = result.get(timeout=30)
    for i, res in enumerate(results):
        print(f"Group Task {i+1}: {res}")
    print()


def test_chain_execution():
    """체인 실행 테스트 - 태스크 순차 실행"""
    print("=== 체인 실행 테스트 ===")
    
    # 체인으로 순차 실행 (첫 번째 태스크의 결과가 두 번째 태스크의 입력이 됨)
    workflow = chain(
        simple_task.s("First Task"),
        # 실제로는 이전 결과를 사용하지만, 예제를 위해 새 메시지 사용
        simple_task.s("Second Task"),
        simple_task.s("Third Task")
    )
    
    result = workflow.apply_async()
    print(f"Chain ID: {result.id}")
    print(f"Chain Result: {result.get(timeout=30)}")
    print()


def test_chord_execution():
    """코드 실행 테스트 - 그룹 실행 후 콜백"""
    print("=== 코드 실행 테스트 ===")
    
    # 여러 태스크를 병렬로 실행하고, 모두 완료되면 콜백 실행
    callback = simple_task.s("All tasks completed!")
    
    job = chord([
        simple_task.s(f"Chord Task {i}")
        for i in range(3)
    ])(callback)
    
    print(f"Chord ID: {job.id}")
    result = job.get(timeout=30)
    print(f"Chord Result: {result}")
    print()


def test_task_retry():
    """태스크 재시도 테스트"""
    print("=== 태스크 재시도 테스트 ===")
    
    # 실패할 수 있는 태스크 (예: 외부 API 호출)
    result = ai_processing_task.delay("Test retry", 50)
    print(f"Task ID: {result.id}")
    
    try:
        final_result = result.get(timeout=30)
        print(f"Task Result: {final_result}")
    except Exception as e:
        print(f"Task failed: {e}")
    print()


def test_task_revoke():
    """태스크 취소 테스트"""
    print("=== 태스크 취소 테스트 ===")
    
    # 긴 시간 소요 태스크 시작
    result = long_running_task.delay(10)
    print(f"Started long task: {result.id}")
    
    # 3초 후 취소
    time.sleep(3)
    result.revoke(terminate=True)
    print("Task revoked!")
    
    try:
        print(f"Task Status: {result.status}")
    except Exception as e:
        print(f"Error checking revoked task: {e}")
    print()


def test_signature_usage():
    """시그니처 사용 테스트"""
    print("=== 시그니처 사용 테스트 ===")
    
    # 시그니처 생성 (태스크의 서명)
    sig = signature('app.tasks.simple_task', args=['Signature test'])
    
    # 나중에 실행
    result = sig.apply_async()
    print(f"Signature Task ID: {result.id}")
    print(f"Signature Result: {result.get(timeout=10)}")
    print()


def test_eta_and_countdown():
    """ETA와 카운트다운 테스트"""
    print("=== ETA와 카운트다운 테스트 ===")
    
    # 5초 후 실행
    result1 = simple_task.apply_async(
        args=['Delayed task'],
        countdown=5
    )
    print(f"Delayed task ID: {result1.id} (will execute in 5 seconds)")
    
    # 특정 시간에 실행 (현재 시간 + 3초)
    import datetime
    eta = datetime.datetime.now() + datetime.timedelta(seconds=3)
    result2 = simple_task.apply_async(
        args=['ETA task'],
        eta=eta
    )
    print(f"ETA task ID: {result2.id} (will execute at {eta})")
    
    # 결과 대기
    print("Waiting for delayed tasks...")
    print(f"Delayed Result: {result1.get(timeout=30)}")
    print(f"ETA Result: {result2.get(timeout=30)}")
    print()


def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 Celery 메소드 테스트 시작")
    print("=" * 50)
    
    try:
        test_basic_task()
        test_multiple_tasks()
        test_group_execution()
        test_chain_execution()
        test_chord_execution()
        test_signature_usage()
        test_eta_and_countdown()
        test_task_status()
        test_task_with_progress()
        test_task_retry()
        test_task_revoke()
        
        print("✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")


def interactive_test():
    """대화형 테스트 환경"""
    print("🎯 대화형 Celery 테스트 환경")
    print("=" * 50)
    
    while True:
        print("\n선택할 테스트:")
        print("1. 기본 태스크")
        print("2. 진행률 추적 태스크")
        print("3. 여러 태스크 동시 실행")
        print("4. 그룹 실행")
        print("5. 체인 실행")
        print("6. 코드 실행")
        print("7. 태스크 취소")
        print("8. 지연 실행")
        print("9. 모든 테스트 실행")
        print("0. 종료")
        
        choice = input("\n선택 (0-9): ").strip()
        
        if choice == '1':
            test_basic_task()
        elif choice == '2':
            test_task_with_progress()
        elif choice == '3':
            test_multiple_tasks()
        elif choice == '4':
            test_group_execution()
        elif choice == '5':
            test_chain_execution()
        elif choice == '6':
            test_chord_execution()
        elif choice == '7':
            test_task_revoke()
        elif choice == '8':
            test_eta_and_countdown()
        elif choice == '9':
            run_all_tests()
        elif choice == '0':
            print("테스트 종료!")
            break
        else:
            print("잘못된 선택입니다.")


if __name__ == "__main__":
    print("Celery 테스트 환경에 오신 것을 환영합니다!")
    print("Redis 서버와 Celery 워커가 실행 중인지 확인하세요.")
    print()
    
    mode = input("모드 선택 - 'auto' (모든 테스트 자동 실행) 또는 'interactive' (대화형): ").strip().lower()
    
    if mode == 'auto':
        run_all_tests()
    else:
        interactive_test()