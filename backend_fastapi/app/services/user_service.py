# services/user_service.py


class UserService:
    def __init__(self):
        return



# 전역 서비스 인스턴스
user_service = UserService()

# 의존성 주입 함수
def get_user_service() -> UserService:
    """User 서비스 의존성"""
    return user_service
