# tests/test_task_dependencies.py

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.tasks_router import router
from app.dependencies import get_task_service

# 테스트용 FastAPI 앱 생성
app = FastAPI()
app.include_router(router)


class MockTaskService:
    """Mock TaskService 클래스"""
    
    def create_example_task(self, message: str, delay: int):
        return {
            "task_id": "mock-task-123",
            "status": "PENDING",
            "message": "Mock task created"
        }
    
    def get_task_status(self, task_id: str):
        if task_id == "valid-task-123":
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": {"message": "Mock task completed"},
                "message": "Task completed successfully"
            }
        else:
            return {
                "task_id": task_id,
                "status": "PENDING",
                "message": "Task is waiting"
            }
    
    def list_active_tasks(self):
        return {
            "active_tasks": [
                {
                    "task_id": "mock-active-1",
                    "name": "app.tasks.example_task",
                    "worker": "worker1"
                }
            ],
            "total_count": 1
        }
    
    def get_tasks_history(self, hours=1, status=None, task_name=None, limit=100):
        return {
            "tasks": [
                {
                    "task_id": "history-1",
                    "status": "SUCCESS",
                    "task_name": "app.tasks.example_task"
                }
            ],
            "statistics": {
                "total_found": 1,
                "returned_count": 1,
                "time_range": f"Last {hours} hour(s)",
                "by_status": {"SUCCESS": 1}
            }
        }


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Mock 서비스 인스턴스"""
    return MockTaskService()


def test_create_example_task_with_mock_service(client, mock_service):
    """예제 태스크 생성 - Mock 서비스 사용"""
    # Dependencies Override
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    response = client.post("/example", json={
        "message": "test message",
        "delay": 3
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["task_id"] == "mock-task-123"
    assert data["data"]["status"] == "PENDING"
    
    # 정리
    app.dependency_overrides.clear()


def test_get_task_status_with_valid_id(client, mock_service):
    """태스크 상태 조회 - 유효한 ID"""
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    response = client.get("/status/valid-task-123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["task_id"] == "valid-task-123"
    assert data["data"]["status"] == "SUCCESS"
    
    app.dependency_overrides.clear()


def test_get_task_status_with_invalid_id(client, mock_service):
    """태스크 상태 조회 - 잘못된 ID (너무 짧음)"""
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    response = client.get("/status/123")  # 5글자 미만
    
    assert response.status_code == 400
    error_data = response.json()
    assert "Invalid task ID format" in error_data["detail"]
    
    app.dependency_overrides.clear()


def test_list_active_tasks_with_mock(client, mock_service):
    """활성 태스크 목록 조회 - Mock 사용"""
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    response = client.get("/list")
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total_count"] == 1
    assert len(data["data"]["active_tasks"]) == 1
    assert data["data"]["active_tasks"][0]["task_id"] == "mock-active-1"
    
    app.dependency_overrides.clear()


def test_history_with_invalid_status(client, mock_service):
    """히스토리 조회 - 잘못된 상태 필터"""
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    # 잘못된 상태값으로 요청
    response = client.get("/history?status=INVALID_STATUS")
    
    assert response.status_code == 400
    error_data = response.json()
    assert "Invalid status" in error_data["detail"]
    
    app.dependency_overrides.clear()


def test_history_with_valid_params(client, mock_service):
    """히스토리 조회 - 유효한 파라미터"""
    app.dependency_overrides[get_task_service] = lambda: mock_service
    
    response = client.get("/history?hours=2&status=SUCCESS&limit=50")
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["statistics"]["total_found"] == 1
    assert data["data"]["statistics"]["time_range"] == "Last 2 hour(s)"
    
    app.dependency_overrides.clear()


def test_different_service_implementations(client):
    """다른 서비스 구현체 테스트"""
    
    # 첫 번째 서비스 구현체
    class ServiceV1(MockTaskService):
        def create_example_task(self, message: str, delay: int):
            return {"task_id": "v1-task", "version": "v1"}
    
    # 두 번째 서비스 구현체  
    class ServiceV2(MockTaskService):
        def create_example_task(self, message: str, delay: int):
            return {"task_id": "v2-task", "version": "v2"}
    
    # V1 테스트
    app.dependency_overrides[get_task_service] = lambda: ServiceV1()
    response = client.post("/example", json={"message": "test", "delay": 1})
    assert response.json()["data"]["version"] == "v1"
    
    # V2로 변경
    app.dependency_overrides[get_task_service] = lambda: ServiceV2()
    response = client.post("/example", json={"message": "test", "delay": 1})
    assert response.json()["data"]["version"] == "v2"
    
    app.dependency_overrides.clear()


def test_service_error_handling(client):
    """서비스 에러 처리 테스트"""
    
    class ErrorService:
        def create_example_task(self, message: str, delay: int):
            raise Exception("Service error")
    
    app.dependency_overrides[get_task_service] = lambda: ErrorService()
    
    response = client.post("/example", json={"message": "test", "delay": 1})
    
    assert response.status_code == 500
    
    app.dependency_overrides.clear()