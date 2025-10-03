# database.py
from supabase import create_client
from app.config import settings


# 동기용
def get_supabase_sync():
    """Celery 태스크용 동기 Supabase 클라이언트"""
    return create_client(
        settings.NEXT_PUBLIC_SUPABASE_URL, settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
    )


# 비동기용 - FastAPI 비동기 컨텍스트에서도 동기 클라이언트 사용
# 주의: Supabase Python 라이브러리는 완전한 비동기를 지원하지 않음
def get_supabase_async():
    """FastAPI 비동기 종속성 주입용 Supabase 클라이언트 (내부적으로는 동기)"""
    return create_client(
        settings.NEXT_PUBLIC_SUPABASE_URL, settings.NEXT_PUBLIC_SUPABASE_ANON_KEY
    )
