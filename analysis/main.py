"""
分析メインスクリプト
DB からデータを読み込み、分析計算を実行し、結果を保存
"""
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from dotenv import load_dotenv

from analysis.calculations import SectorAnalyzer
from analysis.discord_notifier import DiscordNotifier
from data_ingestion.database import Database

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()


def get_sector_names(db: Database) -> Dict[int, str]:
    """
    セクター名マッピングを取得
    Args:
        db: Database インスタンス
    Returns:
        {sector_id: sector_name}
    """
    try:
        result = db.execute_raw("SELECT id, sector_name FROM sectors ORDER BY id")
        return {row[0]: row[1] for row in result.fetchall()}
    except Exception as e:
        logger.error(f"Failed to fetch sector names: {e}")
        return {}


def get_daily_data_for_date(
    db: Database,
    target_date
) -> tuple:
    """
    指定日付の日次データを取得
    Args:
        db: Database インスタンス
        target_date: 対象日付
    Returns:
        (prices_dict, trading_dict) — {stock_id: [...], ...}
    """
    try:
        # 日次株価を取得
        prices_query = """
            SELECT dp.stock_id, dp.close_price, ms.sector_id
            FROM daily_prices dp
            JOIN master_stocks ms ON dp.stock_id = ms.id
            WHERE dp.date = :date
        """
        prices_result = db.execute_raw(prices_query, {'date': target_date})
        prices_by_stock = {row[0]: (row[1], row[2]) for row in prices_result.fetchall()}

        # 日次売買代金を取得
        trading_query = """
            SELECT dt.stock_id, dt.trading_value_jpy, ms.sector_id
            FROM daily_trading dt
            JOIN master_stocks ms ON dt.stock_id = ms.id
            WHERE dt.date = :date
        """
        trading_result = db.execute_raw(trading_query, {'date': target_date})
        trading_by_stock = {row[0]: (row[1], row[2]) for row in trading_result.fetchall()}

        return prices_by_stock, trading_by_stock

    except Exception as e:
        logger.error(f"Failed to fetch daily data: {e}")
        return {}, {}


def calculate_sector_metrics(
    db: Database,
    target_date,
    sector_names: Dict[int, str]
) -> tuple:
    """
    セクター別指標を計算
    Args:
        db: Database インスタンス
        target_date: 対象日付
        sector_names: セクター名マッピング
    Returns:
        (fund_flow_data, performance_data)
    """
    prices_by_stock, trading_by_stock = get_daily_data_for_date(db, target_date)

    if not prices_by_stock or not trading_by_stock:
        logger.warning(f"No data available for {target_date}")
        return [], []

    # セクター別に集計
    sector_trading_value = {}  # {sector_id: total_trading_value}
    sector_prices = {}  # {sector_id: [prices]}
    sector_stocks = {}  # {sector_id: count}

    for stock_id, (price, sector_id) in prices_by_stock.items():
        if stock_id in trading_by_stock:
            trading_value = trading_by_stock[stock_id][0]

            if sector_id not in sector_trading_value:
                sector_trading_value[sector_id] = 0
                sector_prices[sector_id] = []
                sector_stocks[sector_id] = 0

            sector_trading_value[sector_id] += trading_value or 0
            sector_prices[sector_id].append(price)
            sector_stocks[sector_id] += 1

    # セクター別パフォーマンスを計算（過去 1 日、5 日）
    # TODO: 実装では簡略化のため、今日の株価平均とします
    sector_performance_1d = {}
    sector_fund_flow = []

    for sector_id in sector_trading_value.keys():
        prices = sector_prices.get(sector_id, [])
        trading_value = sector_trading_value[sector_id]

        if prices:
            avg_price = sum(prices) / len(prices)
            # 簡略化：過去データがないため、パフォーマンスは 0 と仮定
            perf_1d = 0.0
            sector_performance_1d[sector_id] = perf_1d

            # 資金流入スコアを計算
            fund_flow_score = trading_value * (1 if perf_1d >= 0 else -1)

            sector_fund_flow.append({
                'sector_id': sector_id,
                'score': fund_flow_score,
                'trading_value': trading_value,
                'perf_1d': perf_1d
            })

    # ランキングを計算
    sector_fund_flow_sorted = sorted(
        sector_fund_flow,
        key=lambda x: x['score'],
        reverse=True
    )

    for rank, item in enumerate(sector_fund_flow_sorted, 1):
        item['rank'] = rank

    return sector_fund_flow_sorted, sector_performance_1d


def main():
    """
    分析メインプロセス
    1. DB からデータ読み込み
    2. セクター別指標を計算
    3. 結果を DB に保存
    4. Discord で通知
    """
    jst = timezone(timedelta(hours=9))
    analysis_date = (datetime.now(tz=jst) - timedelta(days=1)).date()

    logger.info(f"[START] Analysis for {analysis_date}")

    try:
        # Step 1: DB 接続
        db = Database()
        sector_names = get_sector_names(db)

        if not sector_names:
            logger.error("No sectors found in database")
            return

        # Step 2: セクター別指標を計算
        fund_flow_data, performance_data = calculate_sector_metrics(
            db, analysis_date, sector_names
        )

        if not fund_flow_data:
            logger.warning("No sector metrics calculated")
            return

        logger.info(f"Calculated metrics for {len(fund_flow_data)} sectors")

        # Step 3: 結果を DB に保存
        try:
            fund_flow_insert = [
                {
                    'date': analysis_date,
                    'sector_id': item['sector_id'],
                    'fund_flow_amount_jpy': int(item['trading_value']),
                    'fund_flow_rank': item['rank'],
                    'fund_flow_pct_change': float(item.get('perf_1d', 0.0)),
                    'trend_5d': 'up' if item.get('perf_1d', 0) >= 0 else 'down'
                }
                for item in fund_flow_data
            ]
            if fund_flow_insert:
                db.insert_sector_fund_flow(fund_flow_insert)
                logger.info(f"Saved {len(fund_flow_insert)} sector fund flow records")

            perf_insert = [
                {
                    'date': analysis_date,
                    'sector_id': sector_id,
                    'perf_1d': float(perf),
                    'perf_5d': None,
                    'perf_20d': None,
                    'perf_60d': None,
                    'vs_topix_1d': None
                }
                for sector_id, perf in performance_data.items()
            ]
            if perf_insert:
                db.insert_sector_performance(perf_insert)
                logger.info(f"Saved {len(perf_insert)} sector performance records")

        except Exception as e:
            logger.error(f"Failed to save metrics to database: {e}")

        # Step 4: Discord に通知
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        if webhook_url:
            notifier = DiscordNotifier(webhook_url)
            top_inflow = [d for d in fund_flow_data if d['score'] > 0]
            top_outflow = [d for d in fund_flow_data if d['score'] < 0]
            top_outflow.sort(key=lambda x: x['score'])

            perf_changes = {'1d': performance_data}

            notifier.send_daily_summary(
                analysis_date,
                top_inflow,
                top_outflow,
                perf_changes,
                sector_names
            )

        logger.info(f"[SUCCESS] Analysis completed for {analysis_date}")

    except Exception as e:
        logger.error(f"[ERROR] Analysis failed: {e}")
        # Discord にエラーを通知
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        if webhook_url:
            notifier = DiscordNotifier(webhook_url)
            notifier.send_error_alert(f"Analysis error: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
