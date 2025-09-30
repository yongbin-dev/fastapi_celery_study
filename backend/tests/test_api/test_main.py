# tests/test_api/test_main.py
"""
메인 엔드포인트 테스트
"""

from fastapi.testclient import TestClient


class TestMainEndpoints:
    """메인 엔드포인트 테스트 클래스"""

    def test_root_endpoint(self, client: TestClient):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200

        json_response = response.json()
        assert json_response["success"] is True
        assert "name" in json_response["data"]
        assert "version" in json_response["data"]
        assert "docs" in json_response["data"]
        assert "health" in json_response["data"]

    def test_health_check_endpoint(self, client: TestClient):
        """헬스체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200

        json_response = response.json()
        assert json_response["success"] is True
        assert json_response["data"]["status"] == "healthy"
        assert "version" in json_response["data"]
        assert "environment" in json_response["data"]

    def test_version_endpoint(self, client: TestClient):
        """버전 정보 엔드포인트 테스트"""
        response = client.get("/version")
        assert response.status_code == 200

        json_response = response.json()
        assert json_response["success"] is True
        assert "name" in json_response["data"]
        assert "version" in json_response["data"]
        assert "api_version" in json_response["data"]
        assert json_response["data"]["api_version"] == "v1"
