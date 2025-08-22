# topic_config.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class TopicConfig:
    name: str
    handler: str
    group_id: str
    options: Dict[str, Any] = None

# 토픽 설정
TOPIC_CONFIGS = [
    TopicConfig(
        name='python-topic',
        handler='handle_ai_requests',
        group_id='ai-service-group',
        options={'max_poll_records': 10}
    ),
    # TopicConfig(
    #     name='user-messages',
    #     handler='handle_user_messages',
    #     group_id='message-service-group'
    # ),
    # TopicConfig(
    #     name='data-processing',
    #     handler='handle_data_processing',
    #     group_id='data-service-group'
    # ),
    # TopicConfig(
    #     name='notifications',
    #     handler='handle_notifications',
    #     group_id='notification-service-group'
    # )
]