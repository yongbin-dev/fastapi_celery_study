# app/orchestration/workflows/workflow_builder.py
"""
워크플로우 빌더

Celery의 다양한 워크플로우 패턴을 쉽게 구성할 수 있는 빌더 클래스
"""

from typing import Any, Callable, Dict, List

from celery import chain, chord, group


class WorkflowBuilder:
    """워크플로우 빌더 클래스"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.tasks = []

    def add_task(self, task: Callable, *args, **kwargs):
        """순차 태스크 추가"""
        self.tasks.append(task.s(*args, **kwargs))
        return self

    def build_chain(self):
        """Chain 워크플로우 생성 (순차 실행)"""
        if not self.tasks:
            raise ValueError("태스크가 비어있습니다")
        return chain(*self.tasks)

    def build_group(self):
        """Group 워크플로우 생성 (병렬 실행)"""
        if not self.tasks:
            raise ValueError("태스크가 비어있습니다")
        return group(*self.tasks)

    @staticmethod
    def create_chord(parallel_tasks: List, callback_task: Callable):
        """
        Chord 워크플로우 생성 (병렬 실행 후 콜백)

        Args:
            parallel_tasks: 병렬로 실행할 태스크 리스트
            callback_task: 모든 태스크 완료 후 실행할 콜백

        Returns:
            Celery chord 객체
        """
        return chord(parallel_tasks)(callback_task)


class MultiDomainWorkflow:
    """다중 도메인 워크플로우"""

    @staticmethod
    def parallel_processing(image_path: str):
        """
        병렬 처리 워크플로우

        OCR, Vision, LLM을 동시에 실행 후 결과 통합
        """
        from app.domains.ocr.tasks.ocr_tasks import extract_text_task

        # 병렬 실행
        parallel_tasks = group(
            extract_text_task.s(image_path),
        )

        return parallel_tasks

    @staticmethod
    def sequential_processing(input_data: Dict[str, Any]):
        """
        순차 처리 워크플로우

        OCR → LLM → Vision 순서대로 실행
        """
        from app.domains.llm.tasks.llm_tasks import generate_text_task
        from app.domains.ocr.tasks.ocr_tasks import extract_text_task

        # 순차 실행
        sequential_pipeline = chain(
            extract_text_task.s(input_data.get("image_path")),
            generate_text_task.s(),
        )

        return sequential_pipeline
