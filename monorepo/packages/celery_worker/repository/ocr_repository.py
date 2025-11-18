"""OCR 결과 DB 저장 Repository

OCR 결과를 데이터베이스에 저장하는 책임만 담당하는 클래스
"""

from shared.core.database import get_db_manager
from shared.core.logging import get_logger
from shared.pipeline.context import PipelineContext
from shared.repository.crud.sync_crud import (
    ocr_execution_crud,
    ocr_text_box_crud,
)
from shared.repository.crud.sync_crud.batch_execution import batch_execution_crud
from shared.schemas import OCRExecutionCreate
from shared.schemas.ocr_db import OCRTextBoxCreate

logger = get_logger(__name__)


class OCRRepository:
    """OCR 결과 DB 저장 전담 클래스"""

    def save_batch(self, context: PipelineContext):
        """배치 OCR 결과를 DB에 저장

        배치 전체의 chain_id를 사용하고, 각 이미지 처리마다 task_log를 생성합니다.
        트랜잭션 관리 및 에러 핸들링 개선 버전.

        Args:
            context: 파이프라인 컨텍스트
        """
        ocr_results = context.ocr_results
        if not ocr_results or len(ocr_results) == 0:
            logger.warning("OCR 결과가 없어 DB 저장을 건너뜁니다.")
            return

        success_count = 0
        failed_count = 0

        with get_db_manager().get_sync_session() as session:
            if not session:
                raise RuntimeError("DB 세션 생성 실패")

            try:
                # 각 이미지의 OCR 결과를 개별적으로 저장
                for idx, ocr_result in enumerate(ocr_results):
                    try:
                        # private_imgs와 public_file_paths 확인
                        if context.private_imgs is None:
                            logger.warning(
                                f"이미지 {idx}: private_imgs가 없어 건너뜁니다."
                            )
                            failed_count += 1
                            continue

                        image_path = (
                            context.private_imgs[idx]
                            if idx < len(context.private_imgs)
                            else ""
                        )
                        public_path = (
                            context.public_file_paths[idx]
                            if context.public_file_paths
                            and idx < len(context.public_file_paths)
                            else ""
                        )

                        # OCRExecution 생성
                        status = "success" if ocr_result.text_boxes else "failed"
                        error = (
                            "" if ocr_result.text_boxes else "No text boxes extracted"
                        )

                        ocr_execution_data = OCRExecutionCreate(
                            chain_execution_id=context.chain_execution_id,
                            image_path=image_path,
                            public_path=public_path,
                            status=status,
                            error=error,
                        )

                        db_ocr_execution = ocr_execution_crud.create(
                            db=session, obj_in=ocr_execution_data
                        )

                        # 텍스트 박스 저장 (있는 경우에만)
                        text_box_count = 0
                        for box in ocr_result.text_boxes:
                            text_box_data = OCRTextBoxCreate(
                                ocr_execution_id=db_ocr_execution.id,
                                text=box.text,
                                confidence=box.confidence,
                                bbox=box.bbox,
                            )
                            ocr_text_box_crud.create(db=session, obj_in=text_box_data)
                            text_box_count += 1

                        success_count += 1
                        logger.debug(
                            f"이미지 {idx + 1}/{len(ocr_results)} 저장 완료: "
                            f"chain_execution_id={context.chain_execution_id}, "
                            f"text_boxes={text_box_count}"
                        )

                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            f"이미지 {idx + 1}/{len(ocr_results)} 저장 실패: {e}",
                            exc_info=True,
                        )

                        # 개별 이미지 실패는 건너뛰고 계속 진행

                # 모든 이미지 처리 후 한 번만 commit
                session.commit()
                logger.info(
                    f"✅ 배치 OCR 결과 DB 저장 완료: "
                    f"성공 {success_count}개, 실패 {failed_count}개"
                )

                # BatchExecution 진행 상태 업데이트
                self._update_batch_execution(
                    session, context.batch_id, success_count, failed_count
                )

            except Exception as e:
                # 전체 트랜잭션 실패 시 롤백
                session.rollback()
                logger.error(f"❌ 배치 OCR DB 저장 중 오류 발생: {e}", exc_info=True)
                raise

    def _update_batch_execution(
        self, session, batch_id: str, success_count: int, failed_count: int
    ) -> None:
        """BatchExecution 진행 상태 업데이트

        Args:
            session: DB 세션
            batch_id: 배치 ID
            success_count: 성공 개수
            failed_count: 실패 개수
        """
        if not batch_id:
            return

        try:
            batch_execution = batch_execution_crud.get_by_batch_id(
                db=session, batch_id=batch_id
            )
            if batch_execution:
                batch_execution_crud.increment_completed_images(
                    db=session,
                    batch_execution=batch_execution,
                    count=success_count,
                )
                if failed_count > 0:
                    batch_execution_crud.increment_failed_images(
                        db=session,
                        batch_execution=batch_execution,
                        count=failed_count,
                    )
                logger.info(
                    f"📊 BatchExecution 진행 상태 업데이트 완료: "
                    f"batch_id={batch_id}, "
                    f"성공={success_count}, 실패={failed_count}"
                )
            else:
                logger.warning(f"⚠️ BatchExecution을 찾을 수 없음: batch_id={batch_id}")
        except Exception as e:
            logger.error(f"⚠️ BatchExecution 업데이트 실패: {e}", exc_info=True)
            # 진행 상태 업데이트 실패는 치명적이지 않으므로 계속 진행
