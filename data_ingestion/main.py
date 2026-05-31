"""
データ取得メインスクリプト
毎営業日実行：祝日判定 → API データ取得 → DB 保存
"""
import os
import sys
import logging
from datetime import datetime, timedelta, timezone
import jpbizday
from dotenv import load_dotenv

from data_ingestion.database import Database
from data_ingestion.jquants_client import JQuantsDataFetcher

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数読み込み
load_dotenv()


def is_business_day(check_date: datetime.date) -> bool:
    """
    TSE 営業日判定
    Args:
        check_date: 判定対象日
    Returns:
        営業日かどうか
    """
    return jpbizday.is_bizday(check_date)


def main():
    """
    データ取得メインプロセス
    1. 祝日判定
    2. J-Quants API からデータ取得
    3. Supabase に保存
    """
    # Step 1: 営業日判定
    jst = timezone(timedelta(hours=9))
    yesterday = (datetime.now(tz=jst) - timedelta(days=1)).date()

    logger.info(f"Checking if {yesterday} is a business day...")

    if not is_business_day(yesterday):
        logger.info(f"[SKIP] {yesterday} is a holiday or weekend")
        return

    logger.info(f"[START] Data ingestion for {yesterday}")

    # Step 2: API データ取得
    try:
        api_key = os.getenv('JQUANTS_API_KEY')
        if not api_key:
            raise ValueError("JQUANTS_API_KEY environment variable not set")

        fetcher = JQuantsDataFetcher(api_key)
        data = fetcher.fetch_yesterday_data(yesterday)

        if not fetcher.validate_data(data):
            logger.error("Data validation failed")
            return

        logger.info(f"Retrieved data: {len(data['prices'])} prices, {len(data['trading_values'])} trading records")

    except Exception as e:
        logger.error(f"[ERROR] API data fetch failed: {e}")
        raise

    # Step 3: データベースに保存
    try:
        db = Database()

        # 3a. 銘柄マスタを挿入（初回のみ）
        stocks_to_insert = []
        for stock in data.get('stocks', []):
            stocks_to_insert.append({
                'stock_code': stock.get('code'),
                'stock_name': stock.get('name', 'Unknown'),
                'market_tier': stock.get('market_tier', ''),
                'sector_id': int(stock.get('sector', 0)) if stock.get('sector') else None,
                'jquants_code': stock.get('code')
            })

        if stocks_to_insert:
            db.insert_stocks(stocks_to_insert)
            logger.info(f"Inserted/updated {len(stocks_to_insert)} stocks")

        # 3b. 日次株価を挿入
        prices_to_insert = []
        stock_code_to_id = {}

        # stock_code → stock_id のマッピングを作成
        all_stocks = db.get_all_stocks()
        for stock in all_stocks:
            stock_code_to_id[stock['stock_code']] = stock['id']

        for price in data.get('prices', []):
            stock_code = price.get('code')
            stock_id = stock_code_to_id.get(stock_code)

            if not stock_id:
                logger.warning(f"Stock {stock_code} not found in database, skipping price data")
                continue

            prices_to_insert.append({
                'stock_id': stock_id,
                'date': yesterday,
                'open_price': price.get('open'),
                'high_price': price.get('high'),
                'low_price': price.get('low'),
                'close_price': price.get('close'),
                'volume': price.get('volume', 0)
            })

        if prices_to_insert:
            db.insert_daily_prices(prices_to_insert)
            logger.info(f"Inserted {len(prices_to_insert)} daily prices")

        # 3c. 日次売買代金を挿入
        trading_to_insert = []
        for trading in data.get('trading_values', []):
            stock_code = trading.get('code')
            stock_id = stock_code_to_id.get(stock_code)

            if not stock_id:
                continue

            trading_to_insert.append({
                'stock_id': stock_id,
                'date': yesterday,
                'trading_value_jpy': trading.get('trading_value'),
                'vwap': trading.get('vwap')
            })

        if trading_to_insert:
            db.insert_daily_trading(trading_to_insert)
            logger.info(f"Inserted {len(trading_to_insert)} daily trading records")

        logger.info(f"[SUCCESS] Data ingestion completed for {yesterday}")

    except Exception as e:
        logger.error(f"[ERROR] Database insert failed: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
