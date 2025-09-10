# models/task_dependency.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class TaskDependency(Base):
    """
    작업 의존성 테이블
    작업 간의 의존 관계 및 워크플로우 구조 관리
    """
    __tablename__ = "task_dependencies"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    task_id = Column(
        String(255), 
        ForeignKey("task_logs.task_id", ondelete="CASCADE"), 
        index=True,
        nullable=False,
        comment="작업 ID"
    )
    depends_on_task_id = Column(
        String(255), 
        ForeignKey("task_logs.task_id", ondelete="CASCADE"), 
        index=True,
        nullable=False,
        comment="의존하는 작업 ID"
    )
    
    # 의존성 타입
    dependency_type = Column(
        String(50),
        default='sequential',
        comment="의존성 타입 (sequential/parallel/conditional)"
    )
    
    # 조건부 의존성
    condition = Column(
        String(255),
        comment="조건부 의존성 조건 (예: success_only, any_status)"
    )
    
    # 메타데이터
    created_at = Column(
        DateTime, 
        default=datetime.utcnow,
        comment="레코드 생성 시간"
    )
    
    # 관계 설정
    task = relationship(
        "TaskLog", 
        foreign_keys=[task_id], 
        back_populates="dependencies"
    )
    depends_on = relationship(
        "TaskLog", 
        foreign_keys=[depends_on_task_id], 
        back_populates="dependents"
    )
    
    # 제약 조건 및 인덱스
    __table_args__ = (
        UniqueConstraint('task_id', 'depends_on_task_id', name='uq_task_dependency'),
        Index('idx_dependency_type', 'dependency_type'),
    )
    
    def __repr__(self):
        return f"<TaskDependency(task={self.task_id}, depends_on={self.depends_on_task_id}, type={self.dependency_type})>"
    
    @property
    def is_sequential(self):
        """순차적 의존성 여부"""
        return self.dependency_type == 'sequential'
    
    @property
    def is_parallel(self):
        """병렬 의존성 여부"""
        return self.dependency_type == 'parallel'
    
    @property
    def is_conditional(self):
        """조건부 의존성 여부"""
        return self.dependency_type == 'conditional'
    
    def can_proceed(self, depends_on_status):
        """
        진행 가능 여부 확인
        
        Args:
            depends_on_status: 의존 작업의 상태
            
        Returns:
            bool: 진행 가능 여부
        """
        if not self.condition:
            # 조건이 없으면 완료만 확인
            return depends_on_status in ['SUCCESS', 'FAILURE', 'REVOKED']
        
        if self.condition == 'success_only':
            return depends_on_status == 'SUCCESS'
        elif self.condition == 'failure_only':
            return depends_on_status == 'FAILURE'
        elif self.condition == 'any_status':
            return depends_on_status in ['SUCCESS', 'FAILURE', 'REVOKED']
        elif self.condition == 'completed':
            return depends_on_status in ['SUCCESS', 'FAILURE']
        
        return False
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'depends_on_task_id': self.depends_on_task_id,
            'dependency_type': self.dependency_type,
            'condition': self.condition,
            'is_sequential': self.is_sequential,
            'is_parallel': self.is_parallel,
            'is_conditional': self.is_conditional,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_chain(cls, session, task_ids):
        """
        체인 의존성 생성
        
        Args:
            session: DB 세션
            task_ids: 순차적으로 실행될 작업 ID 리스트
        """
        dependencies = []
        for i in range(1, len(task_ids)):
            dep = cls(
                task_id=task_ids[i],
                depends_on_task_id=task_ids[i-1],
                dependency_type='sequential',
                condition='success_only'
            )
            dependencies.append(dep)
            session.add(dep)
        
        return dependencies
    
    @classmethod
    def create_group(cls, session, parent_task_id, child_task_ids):
        """
        그룹 의존성 생성 (하나의 부모에 여러 자식)
        
        Args:
            session: DB 세션
            parent_task_id: 부모 작업 ID
            child_task_ids: 자식 작업 ID 리스트
        """
        dependencies = []
        for child_id in child_task_ids:
            dep = cls(
                task_id=child_id,
                depends_on_task_id=parent_task_id,
                dependency_type='parallel',
                condition='success_only'
            )
            dependencies.append(dep)
            session.add(dep)
        
        return dependencies
    
    @classmethod
    def create_chord(cls, session, group_task_ids, callback_task_id):
        """
        코드 의존성 생성 (그룹 완료 후 콜백)
        
        Args:
            session: DB 세션
            group_task_ids: 그룹 작업 ID 리스트
            callback_task_id: 콜백 작업 ID
        """
        dependencies = []
        for task_id in group_task_ids:
            dep = cls(
                task_id=callback_task_id,
                depends_on_task_id=task_id,
                dependency_type='parallel',
                condition='completed'
            )
            dependencies.append(dep)
            session.add(dep)
        
        return dependencies
    
    @classmethod
    def get_dependency_graph(cls, session, root_task_id, depth=None):
        """
        의존성 그래프 조회
        
        Args:
            session: DB 세션
            root_task_id: 루트 작업 ID
            depth: 탐색 깊이 제한
            
        Returns:
            의존성 그래프 딕셔너리
        """
        def build_graph(task_id, current_depth=0):
            if depth and current_depth >= depth:
                return None
            
            # 현재 작업의 의존성 조회
            deps = session.query(cls).filter_by(depends_on_task_id=task_id).all()
            
            if not deps:
                return None
            
            graph = {}
            for dep in deps:
                graph[dep.task_id] = {
                    'type': dep.dependency_type,
                    'condition': dep.condition,
                    'children': build_graph(dep.task_id, current_depth + 1)
                }
            
            return graph
        
        return {
            root_task_id: {
                'children': build_graph(root_task_id)
            }
        }