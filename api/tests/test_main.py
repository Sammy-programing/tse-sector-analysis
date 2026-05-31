"""
FastAPI テスト
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from datetime import date


@pytest.fixture
def client():
    """テスト用クライアント"""
    return TestClient(app)


# モック DB データ
MOCK_FUND_FLOW = [
    {
        'sector_id': 1,
        'sector_name': '機械・器具',
        'trading_value_jpy': 2500000000,
        'rank': 1,
        'change_1d_pct': 1.5
    },
    {
        'sector_id': 2,
        'sector_name': '電気・ガス業',
        'trading_value_jpy': 1800000000,
        'rank': 2,
        'change_1d_pct': 0.8
    }
]

MOCK_PERFORMANCE = [
    {
        'sector_id': 1,
        'sector_name': '機械・器具',
        'perf_1d': 1.5,
        'perf_5d': 3.2,
        'perf_20d': 5.8,
        'perf_60d': 8.2,
        'vs_topix_1d': 0.8
    },
    {
        'sector_id': 2,
        'sector_name': '電気・ガス業',
        'perf_1d': 0.8,
        'perf_5d': 2.1,
        'perf_20d': 3.5,
        'perf_60d': 5.1,
        'vs_topix_1d': -0.1
    }
]

MOCK_SECTORS = [
    {'sector_id': 1, 'sector_name': '機械・器具'},
    {'sector_id': 2, 'sector_name': '電気・ガス業'}
]


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

    @patch('api.main.Database')
    def test_get_fund_flow(self, mock_db_class, client):
        """GET /api/sectors/fund-flow テスト"""
        mock_db = MagicMock()
        mock_db.get_sector_fund_flow.return_value = MOCK_FUND_FLOW
        mock_db_class.return_value = mock_db

        response = client.get("/api/sectors/fund-flow")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "sectors" in data
        assert len(data["sectors"]) > 0

    @patch('api.main.Database')
    def test_get_fund_flow_with_date(self, mock_db_class, client):
        """GET /api/sectors/fund-flow?date=... テスト"""
        mock_db = MagicMock()
        mock_db.get_sector_fund_flow.return_value = MOCK_FUND_FLOW
        mock_db_class.return_value = mock_db

        response = client.get("/api/sectors/fund-flow?date=2026-05-30")
        assert response.status_code == 200
        data = response.json()
        assert str(data["date"]) == "2026-05-30"

    @patch('api.main.Database')
    def test_fund_flow_response_schema(self, mock_db_class, client):
        """資金流入レスポンス スキーマテスト"""
        mock_db = MagicMock()
        mock_db.get_sector_fund_flow.return_value = MOCK_FUND_FLOW
        mock_db_class.return_value = mock_db

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

    @patch('api.main.Database')
    def test_get_performance(self, mock_db_class, client):
        """GET /api/sectors/performance テスト"""
        mock_db = MagicMock()
        mock_db.get_sector_performance.return_value = MOCK_PERFORMANCE
        mock_db_class.return_value = mock_db

        response = client.get("/api/sectors/performance")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "sectors" in data
        assert "topix_perf_1d" in data

    @patch('api.main.Database')
    def test_performance_response_schema(self, mock_db_class, client):
        """パフォーマンスレスポンス スキーマテスト"""
        mock_db = MagicMock()
        mock_db.get_sector_performance.return_value = MOCK_PERFORMANCE
        mock_db_class.return_value = mock_db

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

    @patch('api.main.Database')
    def test_get_sector_history(self, mock_db_class, client):
        """GET /api/sectors/{sector_id}/history テスト"""
        mock_db = MagicMock()
        mock_db.get_sector_history.return_value = []
        mock_db.get_all_sectors.return_value = MOCK_SECTORS
        mock_db_class.return_value = mock_db

        response = client.get("/api/sectors/1/history")
        assert response.status_code == 200
        data = response.json()
        assert "sector_id" in data
        assert "sector_name" in data
        assert "data" in data

    @patch('api.main.Database')
    def test_get_sector_history_with_dates(self, mock_db_class, client):
        """GET /api/sectors/{sector_id}/history?start_date=...&end_date=... テスト"""
        mock_db = MagicMock()
        mock_db.get_sector_history.return_value = []
        mock_db.get_all_sectors.return_value = MOCK_SECTORS
        mock_db_class.return_value = mock_db

        response = client.get(
            "/api/sectors/1/history?start_date=2026-05-01&end_date=2026-05-30"
        )
        assert response.status_code == 200


class TestMetadataEndpoint:
    """メタデータエンドポイント テスト"""

    @patch('api.main.Database')
    def test_get_sectors_metadata(self, mock_db_class, client):
        """GET /api/metadata/sectors テスト"""
        mock_db = MagicMock()
        mock_db.get_all_sectors.return_value = MOCK_SECTORS
        mock_db_class.return_value = mock_db

        response = client.get("/api/metadata/sectors")
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data
        assert len(data["sectors"]) > 0

        sector = data["sectors"][0]
        assert "sector_id" in sector
        assert "sector_name" in sector
