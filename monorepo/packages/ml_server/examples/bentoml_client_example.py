"""BentoML 클라이언트 사용 예제

BentoML HTTP API를 호출하는 다양한 방법을 보여줍니다.
"""

import asyncio
import json
from pathlib import Path
from typing import List

import httpx
import requests
from PIL import Image


class BentoMLClient:
    """BentoML OCR 서비스 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Args:
            base_url: BentoML 서비스 URL
        """
        self.base_url = base_url

    def health_check(self) -> dict:
        """헬스 체크

        Returns:
            헬스 체크 결과
        """
        response = requests.get(f"{self.base_url}/health_check")
        response.raise_for_status()
        return response.json()

    def extract_text(
        self,
        image_path: str,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> dict:
        """단일 이미지 OCR

        Args:
            image_path: 이미지 파일 경로
            language: OCR 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 텍스트 각도 분류 사용 여부

        Returns:
            OCR 결과
        """
        with open(image_path, "rb") as f:
            files = {"image": f}
            data = {
                "language": language,
                "confidence_threshold": confidence_threshold,
                "use_angle_cls": use_angle_cls,
            }

            response = requests.post(
                f"{self.base_url}/extract_text",
                files=files,
                data=data,
            )
            response.raise_for_status()
            return response.json()

    async def extract_text_async(
        self,
        image_path: str,
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> dict:
        """비동기 단일 이미지 OCR

        Args:
            image_path: 이미지 파일 경로
            language: OCR 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 텍스트 각도 분류 사용 여부

        Returns:
            OCR 결과
        """
        async with httpx.AsyncClient() as client:
            with open(image_path, "rb") as f:
                files = {"image": f}
                data = {
                    "language": language,
                    "confidence_threshold": confidence_threshold,
                    "use_angle_cls": use_angle_cls,
                }

                response = await client.post(
                    f"{self.base_url}/extract_text",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                return response.json()

    def extract_text_batch(
        self,
        image_paths: List[str],
        language: str = "korean",
        confidence_threshold: float = 0.5,
        use_angle_cls: bool = True,
    ) -> dict:
        """배치 이미지 OCR

        Args:
            image_paths: 이미지 파일 경로 리스트
            language: OCR 언어
            confidence_threshold: 신뢰도 임계값
            use_angle_cls: 텍스트 각도 분류 사용 여부

        Returns:
            배치 OCR 결과
        """
        files = [
            ("images", open(path, "rb"))
            for path in image_paths
        ]

        data = {
            "language": language,
            "confidence_threshold": confidence_threshold,
            "use_angle_cls": use_angle_cls,
        }

        response = requests.post(
            f"{self.base_url}/extract_text_batch",
            files=files,
            data=data,
        )
        response.raise_for_status()

        # 파일 닫기
        for _, f in files:
            f.close()

        return response.json()


def example_single_ocr():
    """단일 이미지 OCR 예제"""
    print("\n=== 단일 이미지 OCR ===")

    client = BentoMLClient()

    # 헬스 체크
    health = client.health_check()
    print(f"서비스 상태: {health['status']}")
    print(f"OCR 엔진: {health['engine_type']}")

    # OCR 실행 (실제 이미지 경로로 변경 필요)
    # result = client.extract_text(
    #     image_path="test_image.jpg",
    #     language="korean",
    #     confidence_threshold=0.5,
    # )
    #
    # print(f"\n추출된 텍스트: {result['text']}")
    # print(f"신뢰도: {result['overall_confidence']:.2f}")
    # print(f"텍스트 박스 수: {len(result['text_boxes'])}")
    #
    # # 각 텍스트 박스 출력
    # for i, box in enumerate(result['text_boxes']):
    #     print(f"\n텍스트 박스 {i+1}:")
    #     print(f"  텍스트: {box['text']}")
    #     print(f"  신뢰도: {box['confidence']:.2f}")


async def example_async_ocr():
    """비동기 OCR 예제"""
    print("\n=== 비동기 OCR ===")

    client = BentoMLClient()

    # 여러 이미지를 비동기로 처리
    # tasks = [
    #     client.extract_text_async(f"image_{i}.jpg")
    #     for i in range(5)
    # ]
    #
    # results = await asyncio.gather(*tasks)
    #
    # for i, result in enumerate(results):
    #     print(f"\n이미지 {i+1}: {result['text']}")


def example_batch_ocr():
    """배치 OCR 예제"""
    print("\n=== 배치 OCR ===")

    client = BentoMLClient()

    # 여러 이미지를 한 번에 처리
    # image_paths = [
    #     "image_1.jpg",
    #     "image_2.jpg",
    #     "image_3.jpg",
    # ]
    #
    # result = client.extract_text_batch(image_paths)
    #
    # print(f"총 처리: {result['total_processed']}")
    # print(f"성공: {result['total_success']}")
    # print(f"실패: {result['total_failed']}")
    #
    # for i, ocr_result in enumerate(result['results']):
    #     print(f"\n이미지 {i+1}:")
    #     print(f"  텍스트: {ocr_result['text']}")
    #     print(f"  신뢰도: {ocr_result['overall_confidence']:.2f}")


def example_curl_commands():
    """cURL 명령어 예제"""
    print("\n=== cURL 명령어 예제 ===")

    commands = """
    # 1. 헬스 체크
    curl -X GET "http://localhost:3000/health_check"

    # 2. 단일 이미지 OCR
    curl -X POST "http://localhost:3000/extract_text" \\
      -F "image=@test_image.jpg" \\
      -F "language=korean" \\
      -F "confidence_threshold=0.5" \\
      -F "use_angle_cls=true"

    # 3. Swagger UI 접속
    open http://localhost:3000

    # 4. Prometheus 메트릭
    curl -X GET "http://localhost:3000/metrics"

    # 5. Kubernetes 헬스 체크
    curl -X GET "http://localhost:3000/healthz"
    curl -X GET "http://localhost:3000/readyz"
    curl -X GET "http://localhost:3000/livez"
    """

    print(commands)


if __name__ == "__main__":
    print("BentoML 클라이언트 사용 예제")
    print("=" * 50)

    # 헬스 체크 및 단일 OCR
    example_single_ocr()

    # cURL 명령어 예제
    example_curl_commands()

    # 비동기 OCR (주석 처리)
    # asyncio.run(example_async_ocr())

    # 배치 OCR (주석 처리)
    # example_batch_ocr()

    print("\n완료!")
