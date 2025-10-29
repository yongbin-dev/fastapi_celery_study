-- 배치 실행 테이블 생성
CREATE TABLE IF NOT EXISTS batch_executions (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(255) NOT NULL UNIQUE,
    batch_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- 이미지 통계
    total_images INTEGER NOT NULL DEFAULT 0,
    completed_images INTEGER NOT NULL DEFAULT 0,
    failed_images INTEGER NOT NULL DEFAULT 0,

    -- 청크 통계
    total_chunks INTEGER NOT NULL DEFAULT 0,
    completed_chunks INTEGER NOT NULL DEFAULT 0,
    failed_chunks INTEGER NOT NULL DEFAULT 0,
    chunk_size INTEGER NOT NULL DEFAULT 10,

    -- 타임스탬프
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 메타 정보
    initiated_by VARCHAR(100),
    input_data JSON,
    options JSON,
    final_result JSON,
    error_message TEXT
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_batch_executions_batch_id ON batch_executions(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_executions_status ON batch_executions(status);
CREATE INDEX IF NOT EXISTS idx_batch_status_started ON batch_executions(status, started_at);
CREATE INDEX IF NOT EXISTS idx_batch_name_status ON batch_executions(batch_name, status);

-- chain_executions 테이블에 batch_id 컬럼 추가
ALTER TABLE chain_executions
ADD COLUMN IF NOT EXISTS batch_id VARCHAR(255);

-- chain_executions의 batch_id에 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_chain_executions_batch_id ON chain_executions(batch_id);

-- 코멘트 추가
COMMENT ON TABLE batch_executions IS '배치 실행 테이블 - 대량 이미지 배치 처리 상태 및 결과 추적';
COMMENT ON COLUMN batch_executions.batch_id IS '배치 고유 ID';
COMMENT ON COLUMN batch_executions.batch_name IS '배치 이름';
COMMENT ON COLUMN batch_executions.status IS '배치 실행 상태';
COMMENT ON COLUMN batch_executions.total_images IS '총 이미지 수';
COMMENT ON COLUMN batch_executions.completed_images IS '완료된 이미지 수';
COMMENT ON COLUMN batch_executions.failed_images IS '실패한 이미지 수';
COMMENT ON COLUMN batch_executions.total_chunks IS '총 청크 수';
COMMENT ON COLUMN batch_executions.completed_chunks IS '완료된 청크 수';
COMMENT ON COLUMN batch_executions.failed_chunks IS '실패한 청크 수';
COMMENT ON COLUMN batch_executions.chunk_size IS '청크당 이미지 수';
COMMENT ON COLUMN batch_executions.initiated_by IS '시작한 사용자/시스템';
COMMENT ON COLUMN batch_executions.input_data IS '입력 데이터 (이미지 경로 등)';
COMMENT ON COLUMN batch_executions.options IS '파이프라인 옵션';
COMMENT ON COLUMN batch_executions.final_result IS '최종 결과 (JSON)';
COMMENT ON COLUMN batch_executions.error_message IS '오류 메시지';

COMMENT ON COLUMN chain_executions.batch_id IS '배치 ID (배치 실행 시에만 사용)';
