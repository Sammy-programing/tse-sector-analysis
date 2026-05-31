"""
Supabase データベース接続層
"""
import os
import logging
from typing import List, Dict, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)


class Database:
    """Supabase PostgreSQL 接続管理"""

    def __init__(self):
        """初期化：環境変数から接続情報を取得"""
        db_type = os.getenv('DATABASE_TYPE', 'supabase')

        if db_type == 'supabase':
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')

            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")

            # Supabase PostgreSQL 接続 URL を構築
            project_id = url.split('.supabase.co')[0].replace('https://', '')
            db_url = f"postgresql://postgres.{project_id}:{key}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

            self.engine = create_engine(
                db_url,
                echo=False,
                connect_args={"sslmode": "require"},
                pool_pre_ping=True,
                pool_recycle=3600
            )
        else:
            # SQLite（開発用）
            os.makedirs('data', exist_ok=True)
            self.engine = create_engine('sqlite:///data/market.db', echo=False)

        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized (type={db_type})")

    def get_session(self) -> Session:
        """セッションを取得"""
        return self.SessionLocal()

    def execute_raw(self, query: str, params: Optional[Dict] = None) -> any:
        """Raw SQL を実行"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result

    def insert_stocks(self, stocks: List[Dict]) -> int:
        """
        銘柄マスタを一括挿入
        Args:
            stocks: [{'stock_code': '1001', 'stock_name': '...', 'sector_id': 1, ...}]
        Returns:
            挿入した件数
        """
        if not stocks:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO master_stocks (stock_code, stock_name, market_tier, sector_id, jquants_code)
            VALUES (:stock_code, :stock_name, :market_tier, :sector_id, :jquants_code)
            ON CONFLICT (stock_code) DO UPDATE SET
                stock_name = EXCLUDED.stock_name,
                market_tier = EXCLUDED.market_tier,
                sector_id = EXCLUDED.sector_id,
                updated_at = CURRENT_TIMESTAMP
            """
            for stock in stocks:
                session.execute(text(query), stock)
            session.commit()
            logger.info(f"Inserted {len(stocks)} stocks")
            return len(stocks)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting stocks: {e}")
            raise
        finally:
            session.close()

    def insert_daily_prices(self, prices: List[Dict]) -> int:
        """
        日次株価を一括挿入
        Args:
            prices: [{'stock_id': 1, 'date': '2026-05-30', 'close_price': 101.0, ...}]
        Returns:
            挿入した件数
        """
        if not prices:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO daily_prices (stock_id, date, open_price, high_price, low_price, close_price, volume)
            VALUES (:stock_id, :date, :open_price, :high_price, :low_price, :close_price, :volume)
            ON CONFLICT (stock_id, date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume
            """
            for price in prices:
                session.execute(text(query), price)
            session.commit()
            logger.info(f"Inserted {len(prices)} daily prices")
            return len(prices)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting daily prices: {e}")
            raise
        finally:
            session.close()

    def insert_daily_trading(self, trading: List[Dict]) -> int:
        """
        日次売買代金を一括挿入
        Args:
            trading: [{'stock_id': 1, 'date': '2026-05-30', 'trading_value_jpy': 1000000, ...}]
        Returns:
            挿入した件数
        """
        if not trading:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO daily_trading (stock_id, date, trading_value_jpy, vwap)
            VALUES (:stock_id, :date, :trading_value_jpy, :vwap)
            ON CONFLICT (stock_id, date) DO UPDATE SET
                trading_value_jpy = EXCLUDED.trading_value_jpy,
                vwap = EXCLUDED.vwap
            """
            for record in trading:
                session.execute(text(query), record)
            session.commit()
            logger.info(f"Inserted {len(trading)} daily trading records")
            return len(trading)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting daily trading: {e}")
            raise
        finally:
            session.close()

    def get_stock_id_by_code(self, stock_code: str) -> Optional[int]:
        """
        証券コードから stock_id を取得
        Args:
            stock_code: '1001' など
        Returns:
            stock_id または None
        """
        session = self.get_session()
        try:
            query = "SELECT id FROM master_stocks WHERE stock_code = :code"
            result = session.execute(text(query), {'code': stock_code}).fetchone()
            return result[0] if result else None
        finally:
            session.close()

    def get_all_stocks(self) -> List[Dict]:
        """全銘柄を取得"""
        session = self.get_session()
        try:
            query = "SELECT id, stock_code, sector_id FROM master_stocks ORDER BY stock_code"
            results = session.execute(text(query)).fetchall()
            return [{'id': r[0], 'stock_code': r[1], 'sector_id': r[2]} for r in results]
        finally:
            session.close()

    def insert_sector_aggregates(self, aggregates: List[Dict]) -> int:
        """
        セクター別集計データを挿入
        Args:
            aggregates: [{'date': '2026-05-30', 'sector_id': 1, 'total_trading_value_jpy': ..., ...}]
        """
        if not aggregates:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO sector_daily_aggregates (date, sector_id, total_trading_value_jpy, total_volume, stock_count)
            VALUES (:date, :sector_id, :total_trading_value_jpy, :total_volume, :stock_count)
            ON CONFLICT (date, sector_id) DO UPDATE SET
                total_trading_value_jpy = EXCLUDED.total_trading_value_jpy,
                total_volume = EXCLUDED.total_volume,
                stock_count = EXCLUDED.stock_count
            """
            for agg in aggregates:
                session.execute(text(query), agg)
            session.commit()
            logger.info(f"Inserted {len(aggregates)} sector aggregates")
            return len(aggregates)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting sector aggregates: {e}")
            raise
        finally:
            session.close()

    def insert_sector_performance(self, performance: List[Dict]) -> int:
        """
        セクター別パフォーマンスを挿入
        Args:
            performance: [{'date': '2026-05-30', 'sector_id': 1, 'perf_1d': 2.5, ...}]
        """
        if not performance:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO sector_performance (date, sector_id, perf_1d, perf_5d, perf_20d, perf_60d, vs_topix_1d)
            VALUES (:date, :sector_id, :perf_1d, :perf_5d, :perf_20d, :perf_60d, :vs_topix_1d)
            ON CONFLICT (date, sector_id) DO UPDATE SET
                perf_1d = EXCLUDED.perf_1d,
                perf_5d = EXCLUDED.perf_5d,
                perf_20d = EXCLUDED.perf_20d,
                perf_60d = EXCLUDED.perf_60d,
                vs_topix_1d = EXCLUDED.vs_topix_1d
            """
            for perf in performance:
                session.execute(text(query), perf)
            session.commit()
            logger.info(f"Inserted {len(performance)} sector performance records")
            return len(performance)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting sector performance: {e}")
            raise
        finally:
            session.close()

    def insert_sector_fund_flow(self, fund_flow: List[Dict]) -> int:
        """
        セクター別資金流入を挿入
        Args:
            fund_flow: [{'date': '2026-05-30', 'sector_id': 1, 'fund_flow_amount_jpy': ..., ...}]
        """
        if not fund_flow:
            return 0

        session = self.get_session()
        try:
            query = """
            INSERT INTO sector_fund_flow (date, sector_id, fund_flow_amount_jpy, fund_flow_rank, fund_flow_pct_change, trend_5d)
            VALUES (:date, :sector_id, :fund_flow_amount_jpy, :fund_flow_rank, :fund_flow_pct_change, :trend_5d)
            ON CONFLICT (date, sector_id) DO UPDATE SET
                fund_flow_amount_jpy = EXCLUDED.fund_flow_amount_jpy,
                fund_flow_rank = EXCLUDED.fund_flow_rank,
                fund_flow_pct_change = EXCLUDED.fund_flow_pct_change,
                trend_5d = EXCLUDED.trend_5d
            """
            for ff in fund_flow:
                session.execute(text(query), ff)
            session.commit()
            logger.info(f"Inserted {len(fund_flow)} sector fund flow records")
            return len(fund_flow)
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting sector fund flow: {e}")
            raise
        finally:
            session.close()

    def get_sector_fund_flow(self, target_date) -> List[Dict]:
        """
        指定日付のセクター資金流入データを取得
        Args:
            target_date: 対象日付
        Returns:
            [{'sector_id': int, 'sector_name': str, 'trading_value_jpy': int, 'rank': int, 'change_1d_pct': float}]
        """
        session = self.get_session()
        try:
            query = """
            SELECT
              s.id as sector_id,
              s.sector_name,
              f.fund_flow_amount_jpy as trading_value_jpy,
              f.fund_flow_rank as rank,
              f.fund_flow_pct_change as change_1d_pct
            FROM sector_fund_flow f
            JOIN sectors s ON f.sector_id = s.id
            WHERE f.date = :date
            ORDER BY f.fund_flow_rank
            """
            results = session.execute(text(query), {'date': target_date}).fetchall()
            return [
                {
                    'sector_id': r[0],
                    'sector_name': r[1],
                    'trading_value_jpy': r[2],
                    'rank': r[3],
                    'change_1d_pct': float(r[4]) if r[4] else 0.0
                }
                for r in results
            ]
        finally:
            session.close()

    def get_sector_performance(self, target_date) -> List[Dict]:
        """
        指定日付のセクターパフォーマンスデータを取得
        Args:
            target_date: 対象日付
        Returns:
            [{'sector_id': int, 'sector_name': str, 'perf_1d': float, 'perf_5d': float, ...}]
        """
        session = self.get_session()
        try:
            query = """
            SELECT
              s.id as sector_id,
              s.sector_name,
              p.perf_1d, p.perf_5d, p.perf_20d, p.perf_60d, p.vs_topix_1d
            FROM sector_performance p
            JOIN sectors s ON p.sector_id = s.id
            WHERE p.date = :date
            ORDER BY COALESCE(p.perf_1d, 0) DESC
            """
            results = session.execute(text(query), {'date': target_date}).fetchall()
            return [
                {
                    'sector_id': r[0],
                    'sector_name': r[1],
                    'perf_1d': float(r[2]) if r[2] else None,
                    'perf_5d': float(r[3]) if r[3] else None,
                    'perf_20d': float(r[4]) if r[4] else None,
                    'perf_60d': float(r[5]) if r[5] else None,
                    'vs_topix_1d': float(r[6]) if r[6] else None
                }
                for r in results
            ]
        finally:
            session.close()

    def get_sector_history(self, sector_id, start_date, end_date) -> List[Dict]:
        """
        セクターの履歴データを取得
        Args:
            sector_id: セクター ID
            start_date: 開始日付
            end_date: 終了日付
        Returns:
            [{'date': date, 'fund_flow_jpy': int, 'perf_1d': float, 'perf_5d': float}]
        """
        session = self.get_session()
        try:
            query = """
            SELECT
              f.date,
              f.fund_flow_amount_jpy as fund_flow_jpy,
              p.perf_1d,
              p.perf_5d
            FROM sector_fund_flow f
            LEFT JOIN sector_performance p
              ON f.sector_id = p.sector_id AND f.date = p.date
            WHERE f.sector_id = :sector_id
              AND f.date BETWEEN :start_date AND :end_date
            ORDER BY f.date DESC
            """
            results = session.execute(
                text(query),
                {'sector_id': sector_id, 'start_date': start_date, 'end_date': end_date}
            ).fetchall()
            return [
                {
                    'date': str(r[0]),
                    'fund_flow_jpy': r[1],
                    'perf_1d': float(r[2]) if r[2] else None,
                    'perf_5d': float(r[3]) if r[3] else None
                }
                for r in results
            ]
        finally:
            session.close()

    def get_all_sectors(self) -> List[Dict]:
        """
        全セクターを取得
        Returns:
            [{'sector_id': int, 'sector_name': str}]
        """
        session = self.get_session()
        try:
            query = "SELECT id, sector_name FROM sectors ORDER BY id"
            results = session.execute(text(query)).fetchall()
            return [
                {'sector_id': r[0], 'sector_name': r[1]}
                for r in results
            ]
        finally:
            session.close()

    def get_stock_rankings(self, target_date, limit=10) -> List[Dict]:
        """
        指定日付の銘柄売買代金ランキング（Phase 4用）
        Args:
            target_date: 対象日付
            limit: 取得件数
        Returns:
            [{'stock_code': str, 'stock_name': str, 'sector_name': str, 'trading_value_jpy': int, ...}]
        """
        session = self.get_session()
        try:
            query = """
            SELECT
              ms.stock_code,
              ms.stock_name,
              s.sector_name,
              dt.trading_value_jpy,
              COALESCE(dp.close_price, 0) as close_price,
              COALESCE(dp.open_price, 0) as open_price
            FROM daily_trading dt
            JOIN master_stocks ms ON dt.stock_id = ms.id
            JOIN sectors s ON ms.sector_id = s.id
            LEFT JOIN daily_prices dp ON dt.stock_id = dp.stock_id AND dt.date = dp.date
            WHERE dt.date = :date
            ORDER BY dt.trading_value_jpy DESC NULLS LAST
            LIMIT :limit
            """
            results = session.execute(
                text(query),
                {'date': target_date, 'limit': limit}
            ).fetchall()
            return [
                {
                    'stock_code': r[0],
                    'stock_name': r[1],
                    'sector_name': r[2],
                    'trading_value_jpy': r[3],
                    'close_price': float(r[4]) if r[4] else None,
                    'open_price': float(r[5]) if r[5] else None
                }
                for r in results
            ]
        finally:
            session.close()


# グローバルインスタンス
def get_db() -> Database:
    """データベースインスタンスを取得"""
    return Database()
