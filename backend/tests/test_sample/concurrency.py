import threading


# 2. 싱글톤 적용 (Lock 포함)
class SingletonCounter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.value = 0
                cls._instance.lock = threading.Lock()  # 인스턴스에 Lock 추가
        return cls._instance

    def increment(self):
        with self.lock:  # Lock을 이용하여 동기화 처리
            current_value = self.value
            import time

            time.sleep(0.0001)
            self.value = current_value + 1


def worker_with_lock(counter):
    for _ in range(1000):
        counter.increment()


# 테스트 실행
singleton_counter = SingletonCounter()
threads = [
    threading.Thread(target=worker_with_lock, args=(singleton_counter,))
    for _ in range(10)
]

for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Lock 있는 싱글톤 적용 최종 값: {singleton_counter.value} (예상값: 10000)")
# 이 경우, 최종 값은 항상 예상값과 동일하게 나옵니다.
