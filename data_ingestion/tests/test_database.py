import pytest
import os
from data_ingestion.database import Database

@pytest.fixture
def test_db():
    """テスト用データベース"""
    os.environ['DATABASE_TYPE'] = 'sqlite'
    db = Database()
    # スキーマ初期化
    with open('sql/schema.sql', 'r', encoding='utf-8') as f:
        db.execute(f.read())
    yield db
    # クリーンアップ
    db.engine.dispose()
    try:
        os.remove('data/market.db') if os.path.exists('data/market.db') else None
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
    test_db.insert_stocks([test_stock])

    # 確認
    result = test_db.execute("SELECT COUNT(*) FROM master_stocks WHERE stock_code = :code", {'code': '9984'})
    assert result.fetchone()[0] == 1

def test_insert_prices(test_db):
    """価格挿入テスト"""
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
        'stock_id': 1,  # 上で挿入した銘柄の ID
        'date': '2026-05-30',
        'open_price': 100.0,
        'high_price': 102.0,
        'low_price': 99.0,
        'close_price': 101.0,
        'volume': 1000000
    }
    test_db.insert_daily_prices([price])

    # 確認
    result = test_db.execute("SELECT close_price FROM daily_prices WHERE date = :date", {'date': '2026-05-30'})
    assert result.fetchone()[0] == 101.0
