"""
FastAPI テスト
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """テスト用クライアント"""
    return TestClient(app)


class TestRootEndpoint:
    """ルートエンドポイント テスト"""

    def test_root(self, client):
        """GET / テスト"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "version" in response.json()


class TestHealthEndpoint:
    """ヘルスチェック テスト"""

    def test_health_check(self, client):
        """GET /api/health テスト"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "OK"


class TestFundFlowEndpoint:
    """資金流入エンドポイント テスト"""

    def test_get_fund_flow(self, client):
        """GET /api/sectors/fund-flow テスト"""
        response = client.get("/api/sectors/fund-flow")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "sectors" in data
        assert len(data["sectors"]) > 0

    def test_get_fund_flow_with_date(self, client):
        """GET /api/sectors/fund-flow?date=... テスト"""
        response = client.get("/api/sectors/fund-flow?date=2026-05-30")
        assert response.status_code == 200
        data = response.json()
        assert str(data["date"]) == "2026-05-30"

    def test_fund_flow_response_schema(self, client):
        """資金流入レスポンス スキーマテスト"""
        response = client.get("/api/sectors/fund-flow")
        assert response.status_code == 200
        data = response.json()

        # レスポンス構造確認
        assert "sectors" in data
        sector = data["sectors"][0]
        assert "sector_id" in sector
        assert "sector_name" in sector
        assert "trading_value_jpy" in sector
        assert "rank" in sector
        assert "change_1d_pct" in sector


class TestPerformanceEndpoint:
    """パフォーマンスエンドポイント テスト"""

    def test_get_performance(self, client):
        """GET /api/sectors/performance テスト"""
        response = client.get("/api/sectors/performance")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "sectors" in data
        assert "topix_perf_1d" in data

    def test_performance_response_schema(self, client):
        """パフォーマンスレスポンス スキーマテスト"""
        response = client.get("/api/sectors/performance")
        assert response.status_code == 200
        data = response.json()

        sector = data["sectors"][0]
        assert "sector_id" in sector
        assert "sector_name" in sector
        assert "perf_1d" in sector
        assert "perf_5d" in sector
        assert "perf_20d" in sector
        assert "perf_60d" in sector
        assert "vs_topix_1d" in sector


class TestSectorHistoryEndpoint:
    """セクター履歴エンドポイント テスト"""

    def test_get_sector_history(self, client):
        """GET /api/sectors/{sector_id}/history テスト"""
        response = client.get("/api/sectors/1/history")
        assert response.status_code == 200
        data = response.json()
        assert "sector_id" in data
        assert "sector_name" in data
        assert "data" in data

    def test_get_sector_history_with_dates(self, client):
        """GET /api/sectors/{sector_id}/history?start_date=...&end_date=... テスト"""
        response = client.get(
            "/api/sectors/1/history?start_date=2026-05-01&end_date=2026-05-30"
        )
        assert response.status_code == 200


class TestMetadataEndpoint:
    """メタデータエンドポイント テスト"""

    def test_get_sectors_metadata(self, client):
        """GET /api/metadata/sectors テスト"""
        response = client.get("/api/metadata/sectors")
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data
        assert len(data["sectors"]) > 0

        sector = data["sectors"][0]
        assert "id" in sector
        assert "name" in sector
