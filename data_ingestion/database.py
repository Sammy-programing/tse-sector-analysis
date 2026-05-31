import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        db_type = os.getenv('DATABASE_TYPE', 'sqlite')

        if db_type == 'supabase':
            user = os.getenv('SUPABASE_USER')
            password = os.getenv('SUPABASE_PASSWORD')
            db_name = os.getenv('SUPABASE_DB')

            if not all([user, password, db_name]):
                raise ValueError("Missing Supabase config: SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_DB")

            url = f"postgresql://{user}:{password}@db.supabase.co:5432/{db_name}"
            self.engine = create_engine(url)
        else:
            os.makedirs('data', exist_ok=True)
            self.engine = create_engine('sqlite:///data/market.db')

        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def execute(self, query: str, params: dict = None):
        """Raw SQL 実行"""
        with self.engine.connect() as conn:
            # Split multiple statements for SQLite compatibility
            statements = [s.strip() for s in query.split(';') if s.strip()]
            result = None
            for statement in statements:
                result = conn.execute(text(statement), params or {})
            conn.commit()
            return result

    def insert_stocks(self, stocks: list):
        """銘柄マスタ一括挿入"""
        query = """
        INSERT INTO master_stocks (stock_code, stock_name, market_tier, sector_id, jquants_code)
        VALUES (:stock_code, :stock_name, :market_tier, :sector_id, :jquants_code)
        ON CONFLICT (stock_code) DO NOTHING
        """
        session = self.get_session()
        try:
            for stock in stocks:
                session.execute(text(query), stock)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting stocks: {e}")
            raise
        finally:
            session.close()

    def insert_daily_prices(self, prices: list):
        """日次株価一括挿入"""
        query = """
        INSERT INTO daily_prices (stock_id, date, open_price, high_price, low_price, close_price, volume)
        VALUES (:stock_id, :date, :open_price, :high_price, :low_price, :close_price, :volume)
        ON CONFLICT (stock_id, date) DO UPDATE SET
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume
        """
        session = self.get_session()
        try:
            for price in prices:
                session.execute(text(query), price)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting prices: {e}")
            raise
        finally:
            session.close()

# グローバルインスタンス
db = Database()
