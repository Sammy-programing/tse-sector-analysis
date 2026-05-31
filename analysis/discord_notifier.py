"""
Discord 通知モジュール
日次分析結果をメッセージで送信
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import date
from discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord webhook 経由でメッセージ送信"""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        初期化
        Args:
            webhook_url: Discord webhook URL（未指定時は環境変数から取得）
        """
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK')
        if not self.webhook_url:
            logger.warning("Discord webhook URL not set")

    def send_daily_summary(
        self,
        analysis_date: date,
        top_inflow_sectors: List[Dict],
        top_outflow_sectors: List[Dict],
        performance_changes: Dict[str, Dict],
        sector_names: Dict[int, str]
    ):
        """
        日次分析結果を Discord に投稿
        Args:
            analysis_date: 分析日付
            top_inflow_sectors: [{'sector_id': 1, 'score': ...}, ...]
            top_outflow_sectors: [{'sector_id': 2, 'score': ...}, ...]
            performance_changes: {'1d': {1: 2.5, ...}, '5d': {...}}
            sector_names: {1: 'テクノロジー', ...}
        """
        if not self.webhook_url:
            logger.warning("Cannot send Discord notification: webhook URL not set")
            return

        try:
            # メッセージ本文作成
            message = f"📊 **セクター市場分析 — {analysis_date}**\n\n"

            # 流入セクター Top 5
            message += "**💰 資金流入上位 5 セクター:**\n"
            for i, sector_data in enumerate(top_inflow_sectors[:5], 1):
                sector_id = sector_data.get('sector_id')
                sector_name = sector_names.get(sector_id, f"Sector {sector_id}")
                score = sector_data.get('score', 0) / 1e9  # 十億単位
                message += f"{i}. {sector_name}: ¥{score:.1f}B\n"
            message += "\n"

            # 流出セクター Top 5
            message += "**📉 資金流出上位 5 セクター:**\n"
            for i, sector_data in enumerate(top_outflow_sectors[:5], 1):
                sector_id = sector_data.get('sector_id')
                sector_name = sector_names.get(sector_id, f"Sector {sector_id}")
                score = abs(sector_data.get('score', 0)) / 1e9
                message += f"{i}. {sector_name}: -¥{score:.1f}B\n"
            message += "\n"

            # パフォーマンス変動（1日）
            message += "**📈 パフォーマンス変動（1日）:**\n"
            perf_1d = performance_changes.get('1d', {})
            if perf_1d:
                top_performers = sorted(
                    [(sector_names.get(sid, f"Sector {sid}"), perf)
                     for sid, perf in perf_1d.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                for sector_name, perf in top_performers:
                    message += f"- {sector_name}: {perf:+.2f}%\n"
            else:
                message += "- データなし\n"

            message += f"\n🔗 詳細分析: [ダッシュボード](https://github.com)\n"

            # 送信
            webhook = DiscordWebhook(url=self.webhook_url, content=message)
            response = webhook.execute()
            logger.info(f"Discord notification sent for {analysis_date}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def send_error_alert(self, error_message: str):
        """
        エラーアラートを送信
        Args:
            error_message: エラーメッセージ
        """
        if not self.webhook_url:
            logger.warning("Cannot send error alert: webhook URL not set")
            return

        try:
            message = f"⚠️ **分析エラー**\n\n{error_message}"
            webhook = DiscordWebhook(url=self.webhook_url, content=message)
            webhook.execute()
            logger.info("Error alert sent to Discord")
            return True
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")
            return False
