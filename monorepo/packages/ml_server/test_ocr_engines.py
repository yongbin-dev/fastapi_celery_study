#!/usr/bin/env python3
"""
OCR 엔진 테스트 스크립트
EasyOCR과 PaddleOCR 엔진의 기본 기능을 테스트합니다.
"""

import sys
import io
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.engines.OCREngineFactory import OCREngineFactory
from shared.core.logging import get_logger

logger = get_logger(__name__)


def create_test_image() -> bytes:
    """테스트용 간단한 이미지 생성 (PIL 사용)"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 흰색 배경 이미지 생성
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)

        # 텍스트 그리기 (한글 테스트)
        text = "안녕하세요 OCR 테스트"

        # 기본 폰트 사용 (시스템에 따라 다를 수 있음)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()

        draw.text((10, 30), text, fill='black', font=font)

        # 이미지를 바이트로 변환
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr.read()
    except ImportError:
        logger.error("PIL(Pillow) 라이브러리가 필요합니다: pip install Pillow")
        return b""


def test_engine_factory():
    """OCR 엔진 팩토리 테스트"""
    logger.info("\n" + "="*60)
    logger.info("🧪 OCR 엔진 팩토리 테스트")
    logger.info("="*60)

    # 사용 가능한 엔진 목록 확인
    available_engines = OCREngineFactory.get_available_engines()
    logger.info(f"✅ 사용 가능한 엔진: {available_engines}")

    # 각 엔진 생성 테스트
    for engine_type in available_engines:
        logger.info(f"\n🔧 {engine_type} 엔진 생성 테스트...")
        engine = OCREngineFactory.create_engine(engine_type)

        if engine:
            logger.info(f"  ✅ 엔진 생성 성공: {engine.get_engine_name()}")
            logger.info(f"  - 언어: {engine.lang}")
            logger.info(f"  - 각도 보정: {engine.use_angle_cls}")
        else:
            logger.error(f"  ❌ {engine_type} 엔진 생성 실패")


def test_easyocr_engine():
    """EasyOCR 엔진 테스트"""
    logger.info("\n" + "="*60)
    logger.info("🧪 EasyOCR 엔진 테스트")
    logger.info("="*60)

    try:
        # 엔진 생성
        logger.info("1️⃣ EasyOCR 엔진 생성...")
        engine = OCREngineFactory.create_engine("easyocr", lang="korean")

        if not engine:
            logger.error("❌ EasyOCR 엔진 생성 실패")
            return

        logger.info(f"✅ 엔진 생성 완료: {engine.get_engine_name()}")

        # 모델 로드
        logger.info("\n2️⃣ 모델 로딩...")
        engine.load_model()

        if not engine.is_loaded:
            logger.error("❌ 모델 로드 실패")
            return

        logger.info("✅ 모델 로드 완료")

        # 테스트 이미지 생성
        logger.info("\n3️⃣ 테스트 이미지 생성...")
        test_image = create_test_image()

        if not test_image:
            logger.warning("⚠️ 테스트 이미지 생성 실패 - PIL 설치 필요")
            logger.info("테스트 이미지 없이 계속 진행...")
            return

        logger.info(f"✅ 테스트 이미지 생성 완료 ({len(test_image)} bytes)")

        # OCR 실행
        logger.info("\n4️⃣ OCR 실행...")
        result = engine.predict(test_image, confidence_threshold=0.3)

        logger.info(f"\n📊 OCR 결과:")
        logger.info(f"  - 상태: {result.status}")
        logger.info(f"  - 검출된 텍스트 박스 수: {len(result.text_boxes)}")

        if result.error:
            logger.error(f"  - 에러: {result.error}")

        for i, text_box in enumerate(result.text_boxes, 1):
            logger.info(f"\n  📝 텍스트 박스 {i}:")
            logger.info(f"    - 텍스트: {text_box.text}")
            logger.info(f"    - 신뢰도: {text_box.confidence:.3f}")
            logger.info(f"    - 좌표: {text_box.bbox}")

        if result.status == "success" and len(result.text_boxes) > 0:
            logger.info("\n✅ EasyOCR 엔진 테스트 성공!")
        else:
            logger.warning("\n⚠️ EasyOCR 엔진 테스트 완료 (결과 없음)")

    except Exception as e:
        logger.error(f"\n❌ EasyOCR 테스트 중 에러 발생: {str(e)}", exc_info=True)


def test_paddleocr_engine():
    """PaddleOCR 엔진 테스트"""
    logger.info("\n" + "="*60)
    logger.info("🧪 PaddleOCR 엔진 테스트")
    logger.info("="*60)

    try:
        # 설정 확인
        from shared.config import settings

        if not settings.OCR_DET or not settings.OCR_REC:
            logger.warning("⚠️ PaddleOCR 모델 경로가 설정되지 않았습니다.")
            logger.info("OCR_DET 및 OCR_REC 환경 변수를 설정해주세요.")
            return

        # 엔진 생성
        logger.info("1️⃣ PaddleOCR 엔진 생성...")
        engine = OCREngineFactory.create_engine("paddleocr", lang="korean")

        if not engine:
            logger.error("❌ PaddleOCR 엔진 생성 실패")
            return

        logger.info(f"✅ 엔진 생성 완료: {engine.get_engine_name()}")

        # 모델 로드
        logger.info("\n2️⃣ 모델 로딩...")
        engine.load_model()

        if not engine.is_loaded:
            logger.error("❌ 모델 로드 실패")
            return

        logger.info("✅ 모델 로드 완료")

        # 테스트 이미지 생성
        logger.info("\n3️⃣ 테스트 이미지 생성...")
        test_image = create_test_image()

        if not test_image:
            logger.warning("⚠️ 테스트 이미지 생성 실패")
            return

        logger.info(f"✅ 테스트 이미지 생성 완료 ({len(test_image)} bytes)")

        # OCR 실행
        logger.info("\n4️⃣ OCR 실행...")
        result = engine.predict(test_image, confidence_threshold=0.3)

        logger.info(f"\n📊 OCR 결과:")
        logger.info(f"  - 상태: {result.status}")
        logger.info(f"  - 검출된 텍스트 박스 수: {len(result.text_boxes)}")

        if result.error:
            logger.error(f"  - 에러: {result.error}")

        for i, text_box in enumerate(result.text_boxes, 1):
            logger.info(f"\n  📝 텍스트 박스 {i}:")
            logger.info(f"    - 텍스트: {text_box.text}")
            logger.info(f"    - 신뢰도: {text_box.confidence:.3f}")
            logger.info(f"    - 좌표: {text_box.bbox}")

        if result.status == "success":
            logger.info("\n✅ PaddleOCR 엔진 테스트 성공!")
        else:
            logger.warning("\n⚠️ PaddleOCR 엔진 테스트 실패")

    except Exception as e:
        logger.error(f"\n❌ PaddleOCR 테스트 중 에러 발생: {str(e)}", exc_info=True)


def main():
    """메인 테스트 실행"""
    logger.info("\n🚀 OCR 엔진 테스트 시작\n")

    try:
        # 1. 팩토리 테스트
        test_engine_factory()

        # 2. EasyOCR 테스트
        test_easyocr_engine()

        # 3. PaddleOCR 테스트
        test_paddleocr_engine()

        logger.info("\n" + "="*60)
        logger.info("🎉 모든 테스트 완료")
        logger.info("="*60 + "\n")

    except KeyboardInterrupt:
        logger.info("\n\n⚠️ 사용자에 의해 테스트 중단됨")
    except Exception as e:
        logger.error(f"\n❌ 테스트 실행 중 에러: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
