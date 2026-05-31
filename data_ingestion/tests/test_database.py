"""
Database モジュールテスト
"""
import pytest
import os
from data_ingestion.database import Database


@pytest.fixture
def test_db():
    """テスト用データベース（SQLite）"""
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ.pop('SUPABASE_URL', None)
    os.environ.pop('SUPABASE_KEY', None)

    db = Database()

    # スキーマ初期化
    with open('sql/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        for stmt in statements:
            try:
                db.execute_raw(stmt)
            except Exception:
                pass  # 既に存在する場合はスキップ

    yield db

    # クリーンアップ
    db.engine.dispose()
    try:
        if os.path.exists('data/market.db'):
            os.remove('data/market.db')
    except (PermissionError, OSError):
        pass


def test_insert_stocks(test_db):
    """銘柄挿入テスト"""
    test_stock = {
        'stock_code': '9984',
        'stock_name': 'ソフトバンクグループ',
        'market_tier': 'プライム',
        'sector_id': 3,
        'jquants_code': '91910'
    }
    count = test_db.insert_stocks([test_stock])
    assert count == 1

    # 確認
    result = test_db.execute_raw("SELECT COUNT(*) FROM master_stocks WHERE stock_code = :code", {'code': '9984'})
    assert result.fetchone()[0] == 1


def test_insert_daily_prices(test_db):
    """日次株価挿入テスト"""
    # 事前に銘柄を挿入
    test_db.insert_stocks([{
        'stock_code': '9984',
        'stock_name': 'ソフトバンクグループ',
        'market_tier': 'プライム',
        'sector_id': 3,
        'jquants_code': '91910'
    }])

    # 価格を挿入
    price = {
        'stock_id': 1,
        'date': '2026-05-30',
        'open_price': 100.0,
        'high_price': 102.0,
        'low_price': 99.0,
        'close_price': 101.0,
        'volume': 1000000
    }
    count = test_db.insert_daily_prices([price])
    assert count == 1

    # 確認
    result = test_db.execute_raw("SELECT close_price FROM daily_prices WHERE date = :date", {'date': '2026-05-30'})
    assert result.fetchone()[0] == 101.0


def test_get_stock_id_by_code(test_db):
    """株式コード検索テスト"""
    test_db.insert_stocks([{
        'stock_code': '1001',
        'stock_name': 'テスト太郎',
        'market_tier': 'プライム',
        'sector_id': 1,
        'jquants_code': '00010'
    }])

    # デバッグ：挿入されたか確認
    result = test_db.execute_raw("SELECT COUNT(*) FROM master_stocks")
    count = result.fetchone()[0]
    assert count >= 1, f"Expected at least 1 stock, but found {count}"

    stock_id = test_db.get_stock_id_by_code('1001')
    assert stock_id is not None, f"Could not find stock with code 1001"
    assert stock_id >= 1


def test_insert_daily_trading(test_db):
    """日次売買代金挿入テスト"""
    test_db.insert_stocks([{
        'stock_code': '9984',
        'stock_name': 'ソフトバンクグループ',
        'market_tier': 'プライム',
        'sector_id': 3,
        'jquants_code': '91910'
    }])

    trading = {
        'stock_id': 1,
        'date': '2026-05-30',
        'trading_value_jpy': 5000000000,
        'vwap': 100.5
    }
    count = test_db.insert_daily_trading([trading])
    assert count == 1
