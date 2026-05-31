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


# グローバルインスタンス
def get_db() -> Database:
    """データベースインスタンスを取得"""
    return Database()
