#!/usr/bin/env python3
"""
Ollama 연동 테스트 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.config import settings
from app.api.v1.services.model_service import ModelService

def test_environment_config():
    """환경변수 설정 테스트"""
    print(f"🔧 OLLAMA_BASE_URL: {settings.OLLAMA_BASE_URL}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"📊 Model Cache Size: {settings.MODEL_CACHE_SIZE}")

def test_model_service():
    """ModelService 테스트"""
    print("\n🚀 ModelService 초기화 중...")
    service = ModelService()

    print(f"📋 사용 가능한 모델: {service.list_models()}")

    # llama3 모델 테스트
    if "llama3" in service.list_models():
        print("\n🦙 llama3 모델로 테스트 중...")

        test_input = {
            "prompt": "안녕하세요! 간단한 인사를 해주세요.",
        }

        result = service.predict("llama3", test_input)
        print(f"📤 요청: {test_input}")
        print(f"📥 응답: {result}")

        # 템플릿을 사용한 테스트
        print("\n🎯 템플릿을 사용한 테스트...")
        template_input = {
            "prompt": "백엔드 개발자는 왜 항상 커피를 마시나요?",
            "template": "다음 질문에 대해 유머러스하게 답변해줘: {question}"
        }

        template_result = service.predict("llama3", template_input)
        print(f"📤 템플릿 요청: {template_input}")
        print(f"📥 템플릿 응답: {template_result}")
    else:
        print("❌ llama3 모델을 찾을 수 없습니다.")

def test_model_info():
    """모델 정보 테스트"""
    print("\n📋 모델 정보 확인...")
    service = ModelService()

    for model_name in service.list_models():
        info = service.get_model_info(model_name)
        print(f"🔍 {model_name}: {info}")

if __name__ == "__main__":
    print("🔍 Ollama 연동 테스트 시작")
    print("=" * 50)

    try:
        test_environment_config()
        test_model_service()
        test_model_info()
        print("\n✅ 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()