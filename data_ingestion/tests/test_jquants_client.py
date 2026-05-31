"""
J-Quants API クライアント テスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from data_ingestion.jquants_client import JQuantsClient, JQuantsDataFetcher


class TestJQuantsClient:
    """JQuantsClient のテスト"""

    def test_init(self):
        """初期化テスト"""
        client = JQuantsClient('test-key')
        assert client.api_key == 'test-key'
        assert client.session is not None
        client.close()

    @patch('data_ingestion.jquants_client.requests.Session.get')
    def test_get_stocks_info(self, mock_get):
        """銘柄情報取得テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'stocks': [
                {'code': '1001', 'name': '太郎', 'sector': '01'},
                {'code': '1002', 'name': '花子', 'sector': '02'}
            ]
        }
        mock_get.return_value = mock_response

        client = JQuantsClient('test-key')
        stocks = client.get_stocks_info()

        assert len(stocks) == 2
        assert stocks[0]['code'] == '1001'
        mock_get.assert_called_once()
        client.close()

    @patch('data_ingestion.jquants_client.requests.Session.get')
    def test_get_daily_prices(self, mock_get):
        """日次株価取得テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'daily_prices': [
                {
                    'date': '2026-05-30',
                    'code': '1001',
                    'open': 100.0,
                    'high': 102.0,
                    'low': 99.0,
                    'close': 101.0,
                    'volume': 1000000
                }
            ]
        }
        mock_get.return_value = mock_response

        client = JQuantsClient('test-key')
        prices = client.get_daily_prices('2026-05-30')

        assert len(prices) == 1
        assert prices[0]['close'] == 101.0
        client.close()

    @patch('data_ingestion.jquants_client.requests.Session.get')
    def test_get_trading_values(self, mock_get):
        """売買代金取得テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'trading_values': [
                {
                    'date': '2026-05-30',
                    'code': '1001',
                    'trading_value': 5000000000,
                    'vwap': 100.5
                }
            ]
        }
        mock_get.return_value = mock_response

        client = JQuantsClient('test-key')
        trading = client.get_trading_values('2026-05-30')

        assert len(trading) == 1
        assert trading[0]['trading_value'] == 5000000000
        client.close()

    @patch('data_ingestion.jquants_client.requests.Session.get')
    def test_get_indices(self, mock_get):
        """指数データ取得テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'indices': [
                {
                    'date': '2026-05-30',
                    'code': '0001',
                    'open': 2750.0,
                    'high': 2765.0,
                    'low': 2740.0,
                    'close': 2760.0
                }
            ]
        }
        mock_get.return_value = mock_response

        client = JQuantsClient('test-key')
        topix = client.get_indices('2026-05-30')

        assert topix is not None
        assert topix['close'] == 2760.0
        client.close()

    @patch('data_ingestion.jquants_client.requests.Session.get')
    def test_get_indices_not_found(self, mock_get):
        """指数データが見つからない場合"""
        mock_response = Mock()
        mock_response.json.return_value = {'indices': []}
        mock_get.return_value = mock_response

        client = JQuantsClient('test-key')
        topix = client.get_indices('2026-05-30')

        assert topix is None
        client.close()


class TestJQuantsDataFetcher:
    """JQuantsDataFetcher のテスト"""

    @patch.object(JQuantsClient, 'get_stocks_info')
    @patch.object(JQuantsClient, 'get_daily_prices')
    @patch.object(JQuantsClient, 'get_trading_values')
    @patch.object(JQuantsClient, 'get_indices')
    def test_fetch_yesterday_data(self, mock_indices, mock_trading, mock_prices, mock_stocks):
        """日次データ取得テスト"""
        mock_stocks.return_value = [{'code': '1001', 'name': 'テスト'}]
        mock_prices.return_value = [{'code': '1001', 'close': 101.0}]
        mock_trading.return_value = [{'code': '1001', 'trading_value': 1000000}]
        mock_indices.return_value = {'close': 2760.0}

        fetcher = JQuantsDataFetcher('test-key')
        data = fetcher.fetch_yesterday_data(date(2026, 5, 30))

        assert 'stocks' in data
        assert 'prices' in data
        assert 'trading_values' in data
        assert 'topix' in data
        assert data['date'] == '2026-05-30'

    def test_validate_data_valid(self):
        """データ検証テスト（正常系）"""
        fetcher = JQuantsDataFetcher('test-key')
        data = {
            'stocks': [],
            'prices': [{'code': '1001'}],
            'trading_values': [{'code': '1001'}],
            'topix': {}
        }
        assert fetcher.validate_data(data) is True

    def test_validate_data_no_prices(self):
        """データ検証テスト（株価なし）"""
        fetcher = JQuantsDataFetcher('test-key')
        data = {
            'stocks': [],
            'prices': [],
            'trading_values': [{'code': '1001'}],
            'topix': {}
        }
        assert fetcher.validate_data(data) is False

    def test_validate_data_no_trading(self):
        """データ検証テスト（売買代金なし）"""
        fetcher = JQuantsDataFetcher('test-key')
        data = {
            'stocks': [],
            'prices': [{'code': '1001'}],
            'trading_values': [],
            'topix': {}
        }
        assert fetcher.validate_data(data) is False
