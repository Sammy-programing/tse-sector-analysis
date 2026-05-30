import os
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self):
        db_type = os.getenv('DATABASE_TYPE', 'sqlite')

        if db_type == 'supabase':
            self.engine = create_engine(
                f"postgresql://{os.getenv('SUPABASE_USER')}:{os.getenv('SUPABASE_PASSWORD')}"
                f"@db.supabase.co:5432/{os.getenv('SUPABASE_DB')}"
            )
        else:
            # SQLite (開発用)
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
        for stock in stocks:
            session.execute(text(query), stock)
        session.commit()
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
        for price in prices:
            session.execute(text(query), price)
        session.commit()
        session.close()

# グローバルインスタンス
db = Database()
