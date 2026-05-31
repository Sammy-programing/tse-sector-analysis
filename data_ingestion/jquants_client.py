"""
J-Quants API クライアント
JPX 公式の証券データ API を使用
"""
import os
import logging
from datetime import date, timedelta
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class JQuantsClient:
    """J-Quants API クライアント"""

    BASE_URL = "https://api.jquants.com/v1"

    def __init__(self, api_key: str):
        """
        初期化
        Args:
            api_key: J-Quants API キー
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

    def get_stocks_info(self) -> List[Dict]:
        """
        全銘柄情報を取得
        Returns:
            [{'code': '1001', 'name': '太郎', 'sector': '01', ...}]
        """
        url = f"{self.BASE_URL}/stocks"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            stocks = data.get('stocks', [])
            logger.info(f"Retrieved {len(stocks)} stocks from API")
            return stocks
        except requests.RequestException as e:
            logger.error(f"Error fetching stocks info: {e}")
            raise

    def get_daily_prices(self, date_str: str, code: Optional[str] = None) -> List[Dict]:
        """
        指定日付の株価データ取得
        Args:
            date_str: 'YYYY-MM-DD'
            code: 証券コード（省略時は全銘柄）
        Returns:
            [{'date': '...', 'code': '1001', 'open': ..., 'close': ..., 'volume': ...}]
        """
        params = {'date': date_str}
        if code:
            params['code'] = code

        url = f"{self.BASE_URL}/daily_prices"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            prices = data.get('daily_prices', [])
            logger.info(f"Retrieved {len(prices)} price records for {date_str}")
            return prices
        except requests.RequestException as e:
            logger.error(f"Error fetching daily prices: {e}")
            raise

    def get_trading_values(self, date_str: str) -> List[Dict]:
        """
        売買代金データ取得
        Args:
            date_str: 'YYYY-MM-DD'
        Returns:
            [{'date': '...', 'code': '1001', 'trading_value': ..., 'vwap': ...}]
        """
        params = {'date': date_str}
        url = f"{self.BASE_URL}/trading_values"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            trading = data.get('trading_values', [])
            logger.info(f"Retrieved {len(trading)} trading records for {date_str}")
            return trading
        except requests.RequestException as e:
            logger.error(f"Error fetching trading values: {e}")
            raise

    def get_indices(self, date_str: str, code: str = '0001') -> Optional[Dict]:
        """
        指数データ取得（TOPIX など）
        Args:
            date_str: 'YYYY-MM-DD'
            code: '0001' = TOPIX
        Returns:
            {'date': '...', 'open': ..., 'close': ..., 'high': ..., 'low': ...} または None
        """
        params = {'date': date_str, 'code': code}
        url = f"{self.BASE_URL}/indices"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            indices = data.get('indices', [])
            if indices:
                logger.info(f"Retrieved index data for {date_str}")
                return indices[0]
            return None
        except requests.RequestException as e:
            logger.error(f"Error fetching indices: {e}")
            raise

    def close(self):
        """セッションをクローズ"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class JQuantsDataFetcher:
    """J-Quants データ取得オーケストレーター"""

    def __init__(self, api_key: str):
        """
        初期化
        Args:
            api_key: J-Quants API キー
        """
        self.client = JQuantsClient(api_key)

    def fetch_yesterday_data(self, yesterday: date) -> Dict:
        """
        昨日のデータをまとめて取得
        Args:
            yesterday: 昨日の日付
        Returns:
            {
                'stocks': [...],
                'prices': [...],
                'trading_values': [...],
                'topix': {...}
            }
        """
        date_str = yesterday.strftime('%Y-%m-%d')

        try:
            logger.info(f"Fetching data for {date_str}...")

            # 並列取得可能な処理
            stocks = self.client.get_stocks_info()
            prices = self.client.get_daily_prices(date_str)
            trading = self.client.get_trading_values(date_str)
            topix = self.client.get_indices(date_str)

            logger.info(f"Fetched data: {len(prices)} prices, {len(trading)} trading records")

            return {
                'stocks': stocks,
                'prices': prices,
                'trading_values': trading,
                'topix': topix,
                'date': date_str
            }
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise
        finally:
            self.client.close()

    def validate_data(self, data: Dict) -> bool:
        """
        取得したデータを検証
        Args:
            data: fetch_yesterday_data() の戻り値
        Returns:
            有効かどうか
        """
        if not data.get('prices'):
            logger.warning("No price data available")
            return False

        if not data.get('trading_values'):
            logger.warning("No trading data available")
            return False

        return True


def get_fetcher() -> JQuantsDataFetcher:
    """データフェッチャーを取得"""
    api_key = os.getenv('JQUANTS_API_KEY')
    if not api_key:
        raise ValueError("JQUANTS_API_KEY environment variable not set")
    return JQuantsDataFetcher(api_key)
