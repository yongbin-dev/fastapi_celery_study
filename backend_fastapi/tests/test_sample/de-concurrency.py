import threading

# 1. 싱글톤 미적용 (동기화 없음)
class SharedCounter:
    def __init__(self):
        self.value = 0

    def increment(self):
        # 1-1. value를 읽습니다. (경쟁 상태 발생 지점)
        current_value = self.value
        # 1-2. 컨텍스트 스위치 유도 (고의로 지연)
        # 여러 스레드가 동시에 이 부분에 진입하게 만듭니다.
        import time
        time.sleep(0.0001)
        # 1-3. 새로운 값을 업데이트합니다.
        self.value = current_value + 1

def worker_without_lock(counter):
    for _ in range(1000):
        counter.increment()

# 테스트 실행
non_singleton_counter = SharedCounter()
threads = [threading.Thread(target=worker_without_lock, args=(non_singleton_counter,)) for _ in range(10)]

for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Lock 없는 싱글톤 미적용 최종 값: {non_singleton_counter.value} (예상값: 10000)")
# 실제 값은 예상값보다 훨씬 적게 나올 가능성이 높습니다.