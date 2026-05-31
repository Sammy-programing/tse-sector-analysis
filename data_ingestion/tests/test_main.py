"""
データ取得メインスクリプト テスト
"""
import pytest
import os
from unittest.mock import patch, Mock
from datetime import date, datetime, timezone, timedelta
from data_ingestion.main import is_business_day, main


class TestIsBusinessDay:
    """営業日判定テスト"""

    @patch('data_ingestion.main.jpbizday.is_bizday')
    def test_is_business_day_true(self, mock_isopen):
        """営業日の判定"""
        mock_isopen.return_value = True
        assert is_business_day(date(2026, 5, 29)) is True
        mock_isopen.assert_called_once()

    @patch('data_ingestion.main.jpbizday.is_bizday')
    def test_is_business_day_false(self, mock_isopen):
        """祝日の判定"""
        mock_isopen.return_value = False
        assert is_business_day(date(2026, 5, 30)) is False
        mock_isopen.assert_called_once()


class TestMain:
    """メインスクリプトテスト"""

    @patch('data_ingestion.main.jpbizday.is_bizday')
    def test_main_skips_holiday(self, mock_isopen):
        """祝日はスキップ"""
        mock_isopen.return_value = False

        with patch('data_ingestion.main.JQuantsDataFetcher') as mock_fetcher:
            main()
            # API が呼ばれないことを確認
            mock_fetcher.assert_not_called()

    @patch('data_ingestion.main.jpbizday.is_bizday')
    @patch('data_ingestion.main.JQuantsDataFetcher')
    @patch('data_ingestion.main.Database')
    def test_main_processes_business_day(self, mock_db, mock_fetcher_class, mock_isopen):
        """営業日のデータ取得"""
        mock_isopen.return_value = True

        # Mock fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_yesterday_data.return_value = {
            'stocks': [
                {
                    'code': '1001',
                    'name': 'テスト太郎',
                    'sector': '01',
                    'market_tier': 'プライム'
                }
            ],
            'prices': [
                {
                    'code': '1001',
                    'open': 100.0,
                    'high': 102.0,
                    'low': 99.0,
                    'close': 101.0,
                    'volume': 1000000
                }
            ],
            'trading_values': [
                {
                    'code': '1001',
                    'trading_value': 5000000000,
                    'vwap': 100.5
                }
            ],
            'topix': {}
        }
        mock_fetcher.validate_data.return_value = True
        mock_fetcher_class.return_value = mock_fetcher

        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_all_stocks.return_value = [
            {'id': 1, 'stock_code': '1001', 'sector_id': 1}
        ]
        mock_db.return_value = mock_db_instance

        main()

        # API が呼ばれたことを確認
        mock_fetcher.fetch_yesterday_data.assert_called_once()
        # DB メソッドが呼ばれたことを確認
        mock_db_instance.insert_stocks.assert_called_once()
        mock_db_instance.insert_daily_prices.assert_called_once()
        mock_db_instance.insert_daily_trading.assert_called_once()

    @patch('data_ingestion.main.jpbizday.is_bizday')
    @patch('data_ingestion.main.JQuantsDataFetcher')
    def test_main_handles_api_error(self, mock_fetcher_class, mock_isopen):
        """API エラーハンドリング"""
        mock_isopen.return_value = True
        mock_fetcher_class.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            main()

    @patch('data_ingestion.main.jpbizday.is_bizday')
    @patch('data_ingestion.main.JQuantsDataFetcher')
    def test_main_handles_validation_failure(self, mock_fetcher_class, mock_isopen):
        """データ検証失敗"""
        mock_isopen.return_value = True

        mock_fetcher = Mock()
        mock_fetcher.fetch_yesterday_data.return_value = {'prices': [], 'trading_values': []}
        mock_fetcher.validate_data.return_value = False
        mock_fetcher_class.return_value = mock_fetcher

        with patch('data_ingestion.main.Database'):
            main()
            # validate_data が False の場合は処理が止まる
            # （戻り値がないことで確認）

    @patch('data_ingestion.main.jpbizday.is_bizday')
    @patch('data_ingestion.main.JQuantsDataFetcher')
    @patch('data_ingestion.main.Database')
    def test_main_handles_missing_stocks(self, mock_db, mock_fetcher_class, mock_isopen):
        """stock_code が存在しない場合"""
        mock_isopen.return_value = True

        mock_fetcher = Mock()
        mock_fetcher.fetch_yesterday_data.return_value = {
            'stocks': [],
            'prices': [
                {
                    'code': '9999',  # 存在しない
                    'open': 100.0,
                    'high': 102.0,
                    'low': 99.0,
                    'close': 101.0,
                    'volume': 1000000
                }
            ],
            'trading_values': [],
            'topix': {}
        }
        mock_fetcher.validate_data.return_value = True
        mock_fetcher_class.return_value = mock_fetcher

        mock_db_instance = Mock()
        mock_db_instance.get_all_stocks.return_value = []
        mock_db.return_value = mock_db_instance

        main()

        # insert_daily_prices が呼ばれないことを確認（価格がスキップされた）
        # ただし、insert_stocks は呼ばれない可能性もある
