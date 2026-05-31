"""
分析メインスクリプト テスト
"""
import pytest
from unittest.mock import Mock, patch
from datetime import date
from analysis.discord_notifier import DiscordNotifier


class TestDiscordNotifier:
    """Discord 通知テスト"""

    def test_init(self):
        """初期化テスト"""
        notifier = DiscordNotifier("https://discord.com/api/webhooks/test")
        assert notifier.webhook_url == "https://discord.com/api/webhooks/test"

    def test_init_from_env(self):
        """環境変数から取得"""
        with patch.dict('os.environ', {'DISCORD_WEBHOOK': 'https://test.webhook'}):
            notifier = DiscordNotifier()
            assert notifier.webhook_url == 'https://test.webhook'

    @patch('analysis.discord_notifier.DiscordWebhook')
    def test_send_daily_summary(self, mock_webhook_class):
        """日次要約送信テスト"""
        mock_webhook = Mock()
        mock_webhook.execute.return_value = True
        mock_webhook_class.return_value = mock_webhook

        notifier = DiscordNotifier("https://test.webhook")

        sector_names = {
            1: 'テクノロジー',
            2: '金融',
            3: 'エネルギー'
        }

        top_inflow = [
            {'sector_id': 1, 'score': 5000000000},
            {'sector_id': 2, 'score': 3000000000}
        ]

        top_outflow = [
            {'sector_id': 3, 'score': -2000000000}
        ]

        performance_changes = {
            '1d': {1: 2.5, 2: 0.5, 3: -1.2}
        }

        result = notifier.send_daily_summary(
            date(2026, 5, 30),
            top_inflow,
            top_outflow,
            performance_changes,
            sector_names
        )

        assert result is True
        mock_webhook.execute.assert_called_once()

    @patch('analysis.discord_notifier.DiscordWebhook')
    def test_send_daily_summary_no_webhook(self, mock_webhook_class):
        """webhook URL なし"""
        notifier = DiscordNotifier(None)
        with patch.dict('os.environ', {}, clear=True):
            notifier.webhook_url = None
            result = notifier.send_daily_summary(
                date(2026, 5, 30),
                [],
                [],
                {},
                {}
            )
            assert result is None

    @patch('analysis.discord_notifier.DiscordWebhook')
    def test_send_error_alert(self, mock_webhook_class):
        """エラーアラートテスト"""
        mock_webhook = Mock()
        mock_webhook.execute.return_value = True
        mock_webhook_class.return_value = mock_webhook

        notifier = DiscordNotifier("https://test.webhook")
        result = notifier.send_error_alert("Test error message")

        assert result is True
        mock_webhook.execute.assert_called_once()

    @patch('analysis.discord_notifier.DiscordWebhook')
    def test_send_error_alert_webhook_failure(self, mock_webhook_class):
        """webhook 送信失敗"""
        mock_webhook = Mock()
        mock_webhook.execute.side_effect = Exception("Connection failed")
        mock_webhook_class.return_value = mock_webhook

        notifier = DiscordNotifier("https://test.webhook")
        result = notifier.send_error_alert("Test error")

        assert result is False


class TestAnalysisMain:
    """分析メインスクリプトテスト"""

    def test_imports(self):
        """モジュールインポートテスト"""
        from analysis.main import get_sector_names, get_daily_data_for_date, calculate_sector_metrics
        assert callable(get_sector_names)
        assert callable(get_daily_data_for_date)
        assert callable(calculate_sector_metrics)
