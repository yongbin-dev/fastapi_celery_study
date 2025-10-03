-- Supabase 테이블 생성 스크립트
-- chain_executions 테이블 마이그레이션

-- 1. chain_executions 테이블 생성
CREATE TABLE IF NOT EXISTS chain_executions (
    id BIGSERIAL PRIMARY KEY,
    chain_id VARCHAR(255) UNIQUE NOT NULL,
    chain_name VARCHAR(255) NOT NULL,

    -- 상태 관리
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- 작업 통계
    total_tasks INTEGER NOT NULL DEFAULT 0,
    completed_tasks INTEGER NOT NULL DEFAULT 0,
    failed_tasks INTEGER NOT NULL DEFAULT 0,

    -- 타임스탬프
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 메타 정보
    initiated_by VARCHAR(100),
    input_data JSONB,
    final_result JSONB,
    error_message TEXT
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_chain_executions_chain_id ON chain_executions(chain_id);
CREATE INDEX IF NOT EXISTS idx_chain_executions_status ON chain_executions(status);
CREATE INDEX IF NOT EXISTS idx_chain_executions_chain_name ON chain_executions(chain_name);
CREATE INDEX IF NOT EXISTS idx_chain_executions_status_created ON chain_executions(status, created_at);
CREATE INDEX IF NOT EXISTS idx_chain_executions_chain_name_status ON chain_executions(chain_name, status);

-- 3. 자동 updated_at 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. chain_executions 테이블에 트리거 적용
DROP TRIGGER IF EXISTS update_chain_executions_updated_at ON chain_executions;
CREATE TRIGGER update_chain_executions_updated_at
    BEFORE UPDATE ON chain_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 5. task_logs 테이블 생성 (ChainExecution과 연관)
CREATE TABLE IF NOT EXISTS task_logs (
    id BIGSERIAL PRIMARY KEY,
    chain_execution_id BIGINT REFERENCES chain_executions(id) ON DELETE CASCADE,

    -- Celery 태스크 정보
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,

    -- 상태 정보
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    -- 결과 및 에러
    result JSONB,
    error TEXT,
    traceback TEXT,

    -- 타임스탬프
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 메타 정보
    args JSONB,
    kwargs JSONB,
    retries INTEGER DEFAULT 0,
    eta TIMESTAMPTZ
);

-- 6. task_logs 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_chain_execution_id ON task_logs(chain_execution_id);
CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_name ON task_logs(task_name);

-- 7. task_logs 테이블에 트리거 적용
DROP TRIGGER IF EXISTS update_task_logs_updated_at ON task_logs;
CREATE TRIGGER update_task_logs_updated_at
    BEFORE UPDATE ON task_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8. Row Level Security (RLS) 설정 (선택사항)
-- Supabase에서 인증된 사용자만 접근하도록 설정할 수 있습니다
-- ALTER TABLE chain_executions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE task_logs ENABLE ROW LEVEL SECURITY;

-- 9. 정책 생성 예시 (필요시 활성화)
-- CREATE POLICY "Enable read access for authenticated users" ON chain_executions
--     FOR SELECT USING (auth.role() = 'authenticated');

-- CREATE POLICY "Enable insert access for authenticated users" ON chain_executions
--     FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- CREATE POLICY "Enable update access for authenticated users" ON chain_executions
--     FOR UPDATE USING (auth.role() = 'authenticated');

-- 10. 코멘트 추가
COMMENT ON TABLE chain_executions IS 'Celery 체인 실행 추적 테이블';
COMMENT ON TABLE task_logs IS 'Celery 태스크 로그 테이블';
COMMENT ON COLUMN chain_executions.chain_id IS '체인 고유 ID (UUID)';
COMMENT ON COLUMN chain_executions.chain_name IS '체인 이름 (예: ai_processing_pipeline)';
COMMENT ON COLUMN chain_executions.status IS '체인 실행 상태 (PENDING, STARTED, SUCCESS, FAILURE, REVOKED)';
COMMENT ON COLUMN task_logs.task_id IS 'Celery 태스크 고유 ID';
COMMENT ON COLUMN task_logs.chain_execution_id IS '연관된 체인 실행 ID';
