# models/task_result.py
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, LargeBinary, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import json
import pickle
import base64
from .base import Base

class TaskResult(Base):
    """
    작업 결과 저장 테이블
    대용량 결과를 별도로 저장하여 메인 테이블 성능 최적화
    """
    __tablename__ = "task_results"
    
    # 기본 필드
    id = Column(Integer, primary_key=True, comment="고유 식별자")
    task_id: Column[str] = Column(
        String(255), 
        ForeignKey("task_logs.task_id", ondelete="CASCADE"), 
        unique=True,
        index=True,
        nullable=False,
        comment="작업 ID (외래키)"
    )
    
    # 결과 타입 및 데이터
    result_type : Column[str]= Column(
        String(50),
        default='json',
        comment="결과 타입 (json/binary/text/pickle)"
    )
    result_data = Column(
        Text,
        comment="텍스트 형식 결과"
    )
    result_binary = Column(
        LargeBinary,
        comment="바이너리 형식 결과"
    )
    result_size : Column[Integer] = Column(
        Integer,
        comment="결과 크기 (바이트)"
    )
    
    # 메타데이터
    created_at = Column(
        DateTime, 
        default=datetime.now,
        comment="레코드 생성 시간"
    )
    
    # 관계 설정
    task = relationship("TaskLog", back_populates="task_result")
    
    # 인덱스 정의
    __table_args__ = (
        Index('idx_task_results_type', 'result_type'),
        Index('idx_task_results_size', 'result_size'),
    )
    
    def __repr__(self):
        return f"<TaskResult(task_id={self.task_id}, type={self.result_type}, size={self.result_size})>"
    
    @property
    def is_large_result(self):
        """대용량 결과 여부 (1MB 이상)"""
        return self.result_size and self.result_size > 1024 * 1024
    
    def set_result(self, data, result_type='auto'):
        """
        결과 저장
        
        Args:
            data: 저장할 데이터
            result_type: 'json', 'text', 'binary', 'pickle', 'auto'
        """
        if result_type == 'auto':
            # 자동 타입 결정
            if isinstance(data, (dict, list)):
                result_type = 'json'
            elif isinstance(data, str):
                result_type = 'text'
            elif isinstance(data, bytes):
                result_type = 'binary'
            else:
                result_type = 'pickle'
        
        self.result_type = result_type
        
        if result_type == 'json':
            json_str = json.dumps(data, ensure_ascii=False)
            self.result_data = json_str
            self.result_size = len(json_str.encode('utf-8'))
            
        elif result_type == 'text':
            self.result_data = str(data)
            self.result_size = len(self.result_data.encode('utf-8'))
            
        elif result_type == 'binary':
            self.result_binary = data if isinstance(data, bytes) else bytes(data)
            self.result_size = len(self.result_binary)
            
        elif result_type == 'pickle':
            pickled = pickle.dumps(data)
            self.result_binary = pickled
            self.result_size = len(pickled)
            self.result_type = 'pickle'
    
    def get_result(self):
        """
        결과 반환
        
        Returns:
            저장된 결과 데이터
        """
        if self.result_type == 'json':
            return json.loads(self.result_data) if self.result_data else None
            
        elif self.result_type == 'text':
            return self.result_data
            
        elif self.result_type == 'binary':
            return self.result_binary
            
        elif self.result_type == 'pickle':
            return pickle.loads(self.result_binary) if self.result_binary else None
            
        return None
    
    def get_result_preview(self, max_length=100):
        """
        결과 미리보기
        
        Args:
            max_length: 최대 길이
            
        Returns:
            결과 미리보기 문자열
        """
        if self.result_type in ['json', 'text']:
            if self.result_data:
                preview = self.result_data[:max_length]
                if len(self.result_data) > max_length:
                    preview += '...'
                return preview
                
        elif self.result_type == 'binary':
            return f"<Binary data: {self.result_size} bytes>"
            
        elif self.result_type == 'pickle':
            return f"<Pickled object: {self.result_size} bytes>"
            
        return None
    
    def to_dict(self, include_data=False):
        """
        딕셔너리 변환
        
        Args:
            include_data: 실제 데이터 포함 여부
        """
        result = {
            'id': self.id,
            'task_id': self.task_id,
            'result_type': self.result_type,
            'result_size': self.result_size,
            'is_large': self.is_large_result,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_data:
            if self.result_type in ['json', 'text']:
                result['data'] = self.get_result()
            elif self.result_type == 'binary':
                # Base64 인코딩하여 전송
                result['data'] = base64.b64encode(self.result_binary).decode('utf-8') if self.result_binary else None
            elif self.result_type == 'pickle':
                # 보안상 pickle 데이터는 직접 노출하지 않음
                result['data'] = '<Pickled object>'
        else:
            result['preview'] = self.get_result_preview()
            
        return result