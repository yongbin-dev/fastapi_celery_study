-- 배치 실행 기능 롤백

-- chain_executions 테이블에서 batch_id 컬럼 제거
ALTER TABLE chain_executions
DROP COLUMN IF EXISTS batch_id;

-- 인덱스 제거
DROP INDEX IF EXISTS idx_chain_executions_batch_id;
DROP INDEX IF EXISTS idx_batch_name_status;
DROP INDEX IF EXISTS idx_batch_status_started;
DROP INDEX IF EXISTS idx_batch_executions_status;
DROP INDEX IF EXISTS idx_batch_executions_batch_id;

-- batch_executions 테이블 제거
DROP TABLE IF EXISTS batch_executions;
