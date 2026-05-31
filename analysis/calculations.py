"""
セクター別分析計算エンジン
資金流入、パフォーマンス、ランキングを計算
"""
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SectorAnalyzer:
    """セクター別分析エンジン"""

    @staticmethod
    def calculate_fund_flow_score(
        trading_values: Dict[str, float],
        performance_pct: Dict[str, float]
    ) -> Dict[str, float]:
        """
        資金流入スコア計算
        売買代金 × 騰落率の符号で「流入」「流出」を判定

        Args:
            trading_values: {'sector_name': trading_value_jpy}
            performance_pct: {'sector_name': pct_change}
        Returns:
            {'sector_name': fund_flow_score}
        """
        scores = {}
        for sector, value in trading_values.items():
            perf = performance_pct.get(sector, 0)
            # 騰落率の符号で売買代金の方向を決定
            score = value * (1 if perf >= 0 else -1)
            scores[sector] = score
        return scores

    @staticmethod
    def calculate_sector_performance(
        daily_prices: pd.DataFrame,
        window_days: int
    ) -> Dict[str, Optional[float]]:
        """
        セクター別パフォーマンス計算（平均騰落率）
        Args:
            daily_prices: DataFrame with columns ['sector', 'close', 'date']
            window_days: 計算期間（営業日）
        Returns:
            {'sector': performance_pct}
        """
        performance = {}

        if daily_prices.empty:
            return performance

        for sector in daily_prices['sector'].unique():
            sector_data = daily_prices[daily_prices['sector'] == sector].sort_values('date')

            if len(sector_data) < window_days:
                # データ不足の場合は NULL
                performance[sector] = None
                continue

            try:
                start_price = sector_data.iloc[-window_days]['close']
                end_price = sector_data.iloc[-1]['close']

                if start_price <= 0:
                    performance[sector] = None
                    continue

                pct_change = ((end_price - start_price) / start_price) * 100
                performance[sector] = round(pct_change, 2)
            except (KeyError, IndexError, TypeError):
                performance[sector] = None

        return performance

    @staticmethod
    def calculate_vs_topix(
        sector_performance: Dict[str, Optional[float]],
        topix_performance: Optional[float]
    ) -> Dict[str, Optional[float]]:
        """
        TOPIX 比パフォーマンス計算
        Args:
            sector_performance: {'sector': perf_pct}
            topix_performance: TOPIX の騰落率
        Returns:
            {'sector': vs_topix_pct}
        """
        if topix_performance is None:
            topix_performance = 0

        return {
            sector: round((perf - topix_performance), 2) if perf is not None else None
            for sector, perf in sector_performance.items()
        }

    @staticmethod
    def rank_sectors(
        scores: Dict[str, float]
    ) -> Dict[str, int]:
        """
        セクターランキング計算
        Args:
            scores: {'sector': score_value}
        Returns:
            {'sector': rank (1が最高)}
        """
        if not scores:
            return {}

        sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {sector: i + 1 for i, (sector, _) in enumerate(sorted_sectors)}

    @staticmethod
    def calculate_moving_average(
        values: List[float],
        window: int
    ) -> Optional[float]:
        """
        移動平均計算
        Args:
            values: 値のリスト
            window: 期間
        Returns:
            移動平均値
        """
        if not values or len(values) < window:
            return None
        return round(sum(values[-window:]) / window, 2)

    @staticmethod
    def calculate_pct_change(
        current: Optional[float],
        previous: Optional[float]
    ) -> Optional[float]:
        """
        パーセント変化率計算
        Args:
            current: 現在値
            previous: 前日値
        Returns:
            変化率 (%)
        """
        if previous is None or previous == 0:
            return None
        if current is None:
            return None
        return round(((current - previous) / abs(previous)) * 100, 2)


class PerformanceCalculator:
    """パフォーマンス計算（単一セクター）"""

    @staticmethod
    def calculate_daily_change(open_price: float, close_price: float) -> float:
        """
        1 日の騰落率計算
        Args:
            open_price: 始値
            close_price: 終値
        Returns:
            騰落率 (%)
        """
        if open_price <= 0:
            return 0.0
        return round(((close_price - open_price) / open_price) * 100, 2)

    @staticmethod
    def calculate_cumulative_return(
        prices: List[float],
        days: int
    ) -> Optional[float]:
        """
        累積リターン計算
        Args:
            prices: 価格のリスト（昇順）
            days: 計算期間
        Returns:
            累積リターン (%) または None
        """
        if len(prices) < days or days <= 0:
            return None

        start_price = prices[-days]
        end_price = prices[-1]

        if start_price <= 0:
            return None

        return round(((end_price - start_price) / start_price) * 100, 2)

    @staticmethod
    def calculate_volatility(prices: List[float], days: int = 20) -> Optional[float]:
        """
        ボラティリティ計算（標準偏差）
        Args:
            prices: 価格のリスト
            days: 計算期間
        Returns:
            ボラティリティ (%)
        """
        if len(prices) < days or days <= 0:
            return None

        recent_prices = prices[-days:]
        returns = []

        for i in range(1, len(recent_prices)):
            ret = (recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1]
            returns.append(ret)

        if not returns:
            return None

        import statistics
        std_dev = statistics.stdev(returns)
        return round(std_dev * 100, 2)


class DataValidator:
    """データ検証"""

    @staticmethod
    def validate_price(price: float) -> bool:
        """株価の妥当性チェック"""
        return price > 0

    @staticmethod
    def validate_volume(volume: int) -> bool:
        """出来高の妥当性チェック"""
        return volume >= 0

    @staticmethod
    def validate_trading_value(trading_value: int) -> bool:
        """売買代金の妥当性チェック"""
        return trading_value >= 0

    @staticmethod
    def detect_outlier(value: float, mean: float, std: float, threshold: float = 3.0) -> bool:
        """
        外れ値検出（3 シグマルール）
        Args:
            value: 値
            mean: 平均
            std: 標準偏差
            threshold: 閾値
        Returns:
            外れ値かどうか
        """
        if std == 0:
            return False
        z_score = abs((value - mean) / std)
        return z_score > threshold
