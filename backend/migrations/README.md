# Supabase 마이그레이션 가이드

## 개요

이 디렉토리에는 Supabase 데이터베이스 마이그레이션 스크립트가 포함되어 있습니다.

## 마이그레이션 실행 방법

### 1. Supabase SQL Editor를 통한 실행

1. [Supabase Dashboard](https://app.supabase.com/) 접속
2. 프로젝트 선택
3. 좌측 메뉴에서 **SQL Editor** 선택
4. `supabase_create_tables.sql` 파일 내용을 복사하여 붙여넣기
5. **RUN** 버튼 클릭하여 실행

### 2. Supabase CLI를 통한 실행

```bash
# Supabase CLI 설치
npm install -g supabase

# 프로젝트 링크 (처음 한 번만)
supabase link --project-ref your-project-ref

# 마이그레이션 실행
supabase db push
```

### 3. psql을 통한 직접 실행

```bash
# Supabase 연결 정보 확인 (Dashboard > Settings > Database)
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
  -f migrations/supabase_create_tables.sql
```

## 생성되는 테이블

### chain_executions
- Celery 체인 실행 상태를 추적하는 메인 테이블
- `chain_id`: 체인 고유 식별자
- `status`: PENDING, STARTED, SUCCESS, FAILURE, REVOKED
- `total_tasks`, `completed_tasks`, `failed_tasks`: 작업 통계
- `input_data`, `final_result`: JSON 데이터

### task_logs
- 개별 Celery 태스크 로그 테이블
- `chain_execution_id`: chain_executions 외래키
- `task_id`: Celery 태스크 고유 ID
- `status`, `result`, `error`: 태스크 실행 정보

## 인덱스

성능 최적화를 위해 다음 인덱스가 생성됩니다:

- `chain_id` (UNIQUE)
- `status`
- `chain_name`
- `(status, created_at)` 복합 인덱스
- `(chain_name, status)` 복합 인덱스

## 자동 업데이트

`updated_at` 컬럼은 트리거를 통해 자동으로 업데이트됩니다.

## Row Level Security (RLS)

기본적으로 RLS는 비활성화되어 있습니다. 필요시 스크립트의 주석 처리된 부분을 활성화하여 설정할 수 있습니다.

## 롤백

테이블을 삭제하려면:

```sql
DROP TABLE IF EXISTS task_logs CASCADE;
DROP TABLE IF EXISTS chain_executions CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
```

## 확인

마이그레이션이 성공했는지 확인:

```sql
-- 테이블 목록 확인
\dt

-- 테이블 구조 확인
\d chain_executions
\d task_logs

-- 데이터 확인
SELECT * FROM chain_executions LIMIT 5;
SELECT * FROM task_logs LIMIT 5;
```

## 환경 변수 설정

`.env` 파일에 Supabase 연결 정보를 추가하세요:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

## 참고 사항

- Supabase는 PostgreSQL 기반이므로 기존 SQLAlchemy 모델과 호환됩니다
- `created_at`과 `updated_at`은 자동으로 관리됩니다
- JSONB 타입을 사용하여 유연한 데이터 저장이 가능합니다
- 외래키 제약조건으로 데이터 무결성이 보장됩니다
