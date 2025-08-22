# config_based_consumer.py (완전 비동기 버전)
import asyncio
import json
from aiokafka import AIOKafkaConsumer
from .topic_config import TOPIC_CONFIGS, TopicConfig
from app.core.config import settings


class ConfigBasedConsumerManager:
    def __init__(self, model_service=None):
        self.model_service = model_service
        self.running = True

    def get_handler(self, handler_name: str):
        """핸들러 함수 동적 로드"""
        handlers = {
            'handle_ai_requests': self.handle_ai_requests,
            'handle_user_messages': self.handle_user_messages,
            'handle_data_processing': self.handle_data_processing,
            'handle_notifications': self.handle_notifications
        }
        return handlers.get(handler_name)

    async def handle_ai_requests(self, message):
        print(f"AI 요청: {message}")
        if self.model_service:
            try:
                data = json.loads(message)
                result = self.model_service.predict("llm", {
                    "message": data.get("text", "안녕"),
                    "max_length": 100
                })
                print(f"AI 응답: {result}")
            except Exception as e:
                print(f"AI 처리 실패: {e}")

    async def handle_user_messages(self, message):
        print(f"사용자 메시지: {message}")

    async def handle_data_processing(self, message):
        print(f"데이터 처리: {message}")

    async def handle_notifications(self, message):
        print(f"알림: {message}")

    async def start_consumers(self):
        """비동기로 모든 Consumer 시작"""
        tasks = []
        for config in TOPIC_CONFIGS:
            handler = self.get_handler(config.handler)
            if handler:
                task = asyncio.create_task(
                    self._consume_topic(config, handler)
                )
                tasks.append(task)
                print(f"{config.name} Consumer 시작")
        return tasks

    async def _consume_topic(self, config: TopicConfig, handler):
        consumer = AIOKafkaConsumer(
            config.name,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            auto_offset_reset=settings.kafka_auto_offset_reset,
            value_deserializer=lambda x: x.decode('utf-8') if x else None,
            group_id=config.group_id
        )

        await consumer.start()
        try:
            while self.running:
                try:
                    # 메시지 가져오기 (타임아웃 1초)
                    msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
                    if msg.value:
                        await handler(msg.value)
                except asyncio.TimeoutError:
                    # 타임아웃은 정상, 계속 진행
                    continue
                except Exception as e:
                    print(f"{config.name} 에러: {e}")
                    break
        finally:
            await consumer.stop()