"""
分析計算エンジン テスト
"""
import pytest
import pandas as pd
from analysis.calculations import SectorAnalyzer, PerformanceCalculator, DataValidator


class TestSectorAnalyzer:
    """SectorAnalyzer のテスト"""

    def test_calculate_fund_flow_score(self):
        """資金流入スコア計算テスト"""
        trading_values = {
            'テクノロジー': 5000000000,
            '金融': 3000000000,
            'エネルギー': 2000000000
        }
        performance_pct = {
            'テクノロジー': 2.5,   # 上昇
            '金融': -1.2,           # 下落
            'エネルギー': 0.0       # 変動なし
        }

        scores = SectorAnalyzer.calculate_fund_flow_score(trading_values, performance_pct)

        # テクノロジーは正のスコア
        assert scores['テクノロジー'] == 5000000000
        # 金融は負のスコア（下落）
        assert scores['金融'] == -3000000000
        # エネルギーは正のスコア（0 は +1 扱い）
        assert scores['エネルギー'] == 2000000000

    def test_calculate_sector_performance(self):
        """セクター別パフォーマンス計算テスト"""
        data = pd.DataFrame({
            'sector': ['テクノロジー'] * 5,
            'close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'date': pd.date_range('2026-05-26', periods=5)
        })

        perf = SectorAnalyzer.calculate_sector_performance(data, window_days=5)

        # 5 日間で 100 → 104, つまり 4% 上昇
        assert perf['テクノロジー'] == 4.0

    def test_calculate_sector_performance_insufficient_data(self):
        """データ不足の場合"""
        data = pd.DataFrame({
            'sector': ['テクノロジー'] * 2,
            'close': [100.0, 101.0],
            'date': pd.date_range('2026-05-29', periods=2)
        })

        perf = SectorAnalyzer.calculate_sector_performance(data, window_days=5)

        assert perf['テクノロジー'] is None

    def test_rank_sectors(self):
        """セクターランキングテスト"""
        scores = {
            'テクノロジー': 5000000000,
            '金融': 3000000000,
            'エネルギー': 2000000000
        }

        ranks = SectorAnalyzer.rank_sectors(scores)

        assert ranks['テクノロジー'] == 1
        assert ranks['金融'] == 2
        assert ranks['エネルギー'] == 3

    def test_calculate_vs_topix(self):
        """TOPIX 比パフォーマンステスト"""
        sector_perf = {
            'テクノロジー': 2.5,
            '金融': 0.5,
            'エネルギー': None
        }
        topix_perf = 1.0

        vs_topix = SectorAnalyzer.calculate_vs_topix(sector_perf, topix_perf)

        assert vs_topix['テクノロジー'] == 1.5
        assert vs_topix['金融'] == -0.5
        assert vs_topix['エネルギー'] is None

    def test_calculate_moving_average(self):
        """移動平均テスト"""
        values = [100.0, 101.0, 102.0, 103.0, 104.0]
        ma = SectorAnalyzer.calculate_moving_average(values, window=3)
        # 最後の 3 個の平均: (102 + 103 + 104) / 3 = 103
        assert ma == 103.0

    def test_calculate_moving_average_insufficient_data(self):
        """移動平均：データ不足"""
        values = [100.0, 101.0]
        ma = SectorAnalyzer.calculate_moving_average(values, window=5)
        assert ma is None

    def test_calculate_pct_change(self):
        """パーセント変化率テスト"""
        pct = SectorAnalyzer.calculate_pct_change(110.0, 100.0)
        assert pct == 10.0

        pct = SectorAnalyzer.calculate_pct_change(90.0, 100.0)
        assert pct == -10.0

    def test_calculate_pct_change_zero_previous(self):
        """パーセント変化率：前日値がゼロ"""
        pct = SectorAnalyzer.calculate_pct_change(100.0, 0)
        assert pct is None


class TestPerformanceCalculator:
    """PerformanceCalculator のテスト"""

    def test_calculate_daily_change(self):
        """1 日騰落率テスト"""
        change = PerformanceCalculator.calculate_daily_change(100.0, 102.0)
        assert change == 2.0

        change = PerformanceCalculator.calculate_daily_change(100.0, 98.0)
        assert change == -2.0

    def test_calculate_daily_change_zero_open(self):
        """1 日騰落率：始値がゼロ"""
        change = PerformanceCalculator.calculate_daily_change(0, 100.0)
        assert change == 0.0

    def test_calculate_cumulative_return(self):
        """累積リターンテスト"""
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        ret = PerformanceCalculator.calculate_cumulative_return(prices, days=5)
        # 100 → 104, つまり 4%
        assert ret == 4.0

    def test_calculate_cumulative_return_insufficient_data(self):
        """累積リターン：データ不足"""
        prices = [100.0, 101.0]
        ret = PerformanceCalculator.calculate_cumulative_return(prices, days=5)
        assert ret is None

    def test_calculate_cumulative_return_zero_start(self):
        """累積リターン：開始価格がゼロ"""
        prices = [0, 100.0, 102.0]
        ret = PerformanceCalculator.calculate_cumulative_return(prices, days=3)
        assert ret is None

    def test_calculate_volatility(self):
        """ボラティリティテスト"""
        prices = [100.0, 101.0, 102.0, 103.0, 104.0] * 5  # 25 日分
        vol = PerformanceCalculator.calculate_volatility(prices, days=20)
        assert vol is not None
        assert vol > 0


class TestDataValidator:
    """DataValidator のテスト"""

    def test_validate_price(self):
        """株価検証テスト"""
        assert DataValidator.validate_price(100.0) is True
        assert DataValidator.validate_price(0) is False
        assert DataValidator.validate_price(-100.0) is False

    def test_validate_volume(self):
        """出来高検証テスト"""
        assert DataValidator.validate_volume(1000000) is True
        assert DataValidator.validate_volume(0) is True
        assert DataValidator.validate_volume(-1000000) is False

    def test_validate_trading_value(self):
        """売買代金検証テスト"""
        assert DataValidator.validate_trading_value(5000000000) is True
        assert DataValidator.validate_trading_value(0) is True
        assert DataValidator.validate_trading_value(-1000000000) is False

    def test_detect_outlier(self):
        """外れ値検出テスト"""
        # 平均 100, 標準偏差 10
        # 値 130 は z-score = 3 で境界線上
        assert DataValidator.detect_outlier(130.0, 100.0, 10.0, threshold=3.0) is False
        # 値 131 は z-score > 3 で外れ値
        assert DataValidator.detect_outlier(131.0, 100.0, 10.0, threshold=3.0) is True
        # 標準偏差 0 の場合
        assert DataValidator.detect_outlier(150.0, 100.0, 0, threshold=3.0) is False
