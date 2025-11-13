"""OCR ML 서버 통신 Client

HTTP/gRPC를 통해 ML 서버와 통신하는 책임만 담당하는 클래스
"""

import json
from typing import List

import httpx
from celery.beat import get_logger

from shared.pipeline.exceptions import RetryableError
from shared.schemas.enums import ProcessStatus
from shared.schemas.ocr_db import OCRExtractDTO

logger = get_logger(__name__)


class OCRClient:
    """ML 서버 통신 전담 클래스"""

    def __init__(self, server_url: str):
        """OCRClient 초기화

        Args:
            server_url: ML 서버 URL
        """
        self.server_url = server_url

    async def call_single(
        self, image_path: str, options: dict
    ) -> OCRExtractDTO:
        """단일 이미지 OCR 요청

        Args:
            image_path: 이미지 경로
            options: OCR 옵션 (language, confidence_threshold, use_angle_cls)

        Returns:
            OCRExtractDTO: OCR 결과

        Raises:
            RetryableError: 서버 오류 (5xx)
            ValueError: 클라이언트 오류 (4xx)
        """
        logger.info(f"단일 BentoML OCR 요청: {image_path}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                request_data = {
                    "private_img": image_path,
                    "language": options.get("language", "korean"),
                    "confidence_threshold": options.get("confidence_threshold", 0.5),
                    "use_angle_cls": options.get("use_angle_cls", True),
                }
                data = {"request_data": json.dumps(request_data)}

                response = await client.post(
                    f"{self.server_url}/extract_text",
                    data=data,
                )

                # 응답 확인
                if response.status_code != 200:
                    error_msg = (
                        f"BentoML API failed: "
                        f"{response.status_code} - {response.text}"
                    )
                    if response.status_code >= 500:
                        raise RetryableError("OCRClient", error_msg)
                    else:
                        raise ValueError(error_msg)

                # JSON 응답 파싱
                result = response.json()

                # OCRExtractDTO로 변환
                text_boxes = self._parse_text_boxes(result.get("text_boxes", []))

                logger.info(f"단일 BentoML OCR 완료: {len(text_boxes)} 텍스트 박스")

                return OCRExtractDTO(
                    text_boxes=text_boxes,
                    status=ProcessStatus.STARTED,
                )

        except httpx.TimeoutException as e:
            raise RetryableError("OCRClient", f"BentoML timeout: {str(e)}") from e
        except httpx.ConnectError as e:
            raise RetryableError(
                "OCRClient", f"BentoML connection error: {str(e)}"
            ) from e

    async def call_batch(
        self, image_paths: List[str], options: dict
    ) -> List[OCRExtractDTO]:
        """배치 이미지 OCR 요청

        Args:
            image_paths: 이미지 경로 리스트
            options: OCR 옵션 (language, confidence_threshold, use_angle_cls)

        Returns:
            List[OCRExtractDTO]: OCR 결과 리스트

        Raises:
            RetryableError: 서버 오류 (5xx)
            ValueError: 클라이언트 오류 (4xx)
        """
        logger.info(f"배치 BentoML OCR 요청: {len(image_paths)}개 이미지")

        # 배치는 타임아웃을 길게 설정 (이미지 개수 * 10초 + 기본 30초)
        timeout = 30.0 + (len(image_paths) * 10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                payload = {
                    "request_data": {
                        "language": options.get("language", "korean"),
                        "confidence_threshold": options.get(
                            "confidence_threshold", 0.5
                        ),
                        "use_angle_cls": options.get("use_angle_cls", True),
                    },
                    "private_imgs": image_paths,
                }

                response = await client.post(
                    f"{self.server_url}/extract_text_batch",
                    json=payload,
                )

                # 응답 확인
                if response.status_code != 200:
                    error_msg = (
                        f"BentoML Batch API failed: "
                        f"{response.status_code} - {response.text}"
                    )

                    if response.status_code >= 500:
                        raise RetryableError("OCRClient", error_msg)
                    else:
                        raise ValueError(error_msg)

                # BatchOCRResponse 파싱
                result = response.json()

                # OCRExtractDTO 리스트로 변환
                ocr_results = []
                for r in result["results"]:
                    text_boxes = self._parse_text_boxes(r.get("text_boxes", []))

                    # 텍스트 박스가 있으면 성공, 없으면 실패로 간주
                    status = (
                        ProcessStatus.STARTED if text_boxes else ProcessStatus.FAILURE
                    )

                    ocr_results.append(
                        OCRExtractDTO(
                            text_boxes=text_boxes,
                            status=status,
                        )
                    )

                logger.info(
                    f"배치 BentoML OCR 완료: {result['total_success']}/"
                    f"{result['total_processed']} 성공"
                )

                return ocr_results

        except httpx.TimeoutException as e:
            raise RetryableError(
                "OCRClient", f"BentoML batch timeout: {str(e)}"
            ) from e
        except httpx.ConnectError as e:
            raise RetryableError(
                "OCRClient", f"BentoML batch connection error: {str(e)}"
            ) from e

    def _parse_text_boxes(self, boxes: List[dict]) -> List[dict]:
        """텍스트 박스 파싱

        Args:
            boxes: 원본 텍스트 박스 리스트

        Returns:
            파싱된 텍스트 박스 리스트
        """
        text_boxes = []
        for box in boxes:
            text_box_dict = {
                "text": box["text"],
                "confidence": box["confidence"],
                "bbox": box["bbox"],
            }
            text_boxes.append(text_box_dict)
        return text_boxes
