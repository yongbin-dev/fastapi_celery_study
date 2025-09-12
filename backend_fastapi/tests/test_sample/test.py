import time

class NonSingleton:
    def __init__(self):
        # 자원을 많이 사용하는 초기화 과정 시뮬레이션
        time.sleep(0.001)

class Singleton:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # 자원 초기화
            time.sleep(0.001)
        return cls._instance

# 성능 테스트 실행
start_time = time.time()
for _ in range(10000):
    NonSingleton()
end_time = time.time()
print(f"Non-Singleton 실행 시간: {end_time - start_time:.4f}초")

start_time = time.time()
for _ in range(10000):
    Singleton()
end_time = time.time()
print(f"Singleton 실행 시간: {end_time - start_time:.4f}초")