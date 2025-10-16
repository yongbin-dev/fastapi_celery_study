# app/domains/ocr/controllers/comparison_controller.py
"""OCR 결과 비교 API 컨트롤러"""

from app.domains.ocr.schemas.similarity import SimilarityRequest, SimilarityResponse
from app.domains.ocr.services.ocr_comparison_service import ocr_comparison_service
from fastapi import APIRouter, Depends
from shared.core.database import get_db
from shared.core.logging import get_logger
from shared.utils.response_builder import ResponseBuilder
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/compare", tags=["OCR Comparison"])


@router.post(
    "",
    response_model=SimilarityResponse,
    summary="OCR 결과 비교",
    description="""
    두 OCR 실행 결과를 비교하여 텍스트 유사도를 측정합니다.
3
    **지원하는 유사도 측정 방법:**
    - `string`: 문자열 기반 유사도 (Levenshtein, Jaro-Winkler, SequenceMatcher)
    - `token`: 토큰 기반 유사도 (Jaccard, Cosine)
    - `all`: 모든 방법 조합 (기본값)

    **가중치 설정 예시:**
    ```json
    {
        "execution_id1": 1,
        "execution_id2": 2,
        "method": "all",
        "weights": {
            "string": 0.5,
            "token": 0.5
        }
    }
    ```
    """,
)
async def compare_ocr_results(
    request: SimilarityRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    두 OCR 실행 결과의 유사도를 측정합니다.

    Args:
        request: 유사도 측정 요청 (execution_id1, execution_id2, method, weights)
        db: 데이터베이스 세션

    Returns:
        SimilarityResponse: 유사도 측정 결과
    """
    try:
        logger.info(
            f"OCR 비교 요청: execution_id1={request.execution_id1}, "
            f"execution_id2={request.execution_id2}, method={request.method}"
        )

        # 유사도 계산
        result = await ocr_comparison_service.compare_executions(
            db=db,
            execution_id1=request.execution_id1,
            execution_id2=request.execution_id2,
            method=request.method,
            weights=request.weights,
        )

        logger.info(
            f"OCR 비교 성공: overall_similarity={result.overall_similarity:.4f}"
        )

        return ResponseBuilder.success(
            data=result, message="OCR 결과 비교가 완료되었습니다."
        )

    except ValueError as e:
        logger.warning(f"OCR 비교 요청 오류: {str(e)}")
        return ResponseBuilder.error(message=str(e), error_code="NOT_FOUND")

    except Exception as e:
        logger.error(f"OCR 비교 중 오류 발생: {str(e)}", exc_info=True)
        return ResponseBuilder.error(
            message=f"OCR 결과 비교 중 오류가 발생했습니다: {str(e)}",
            error_code="INTERNAL_ERROR",
        )
