# 東証セクター資金流入分析プラットフォーム実装計画

> **アジャイルチーム向け:** 本計画はタスク指向設計。各タスクは 2-5 分で完了可能なステップに分割。`superpowers:subagent-driven-development` または `superpowers:executing-plans` でタスク単位に実行してください。

**目標:** 
東証全銘柄の日次株価データから、セクター別の資金流入・パフォーマンスをリアルタイム分析・ダッシュボード表示するプラットフォーム MVP をゼロコストで構築する。

**アーキテクチャ:** 
マイクロサービス 3 層（データ取得 → 分析 → フロントエンド）を GitHub Actions で日次バッチ実行。結果は Supabase PostgreSQL に保存、React で可視化。

**技術スタック:** 
- バックエンド: Python 3.9+, FastAPI (オプション)
- データベース: Supabase PostgreSQL (無料枠) または SQLite (開発用)
- フロントエンド: React 18, Tailwind CSS, Recharts
- インフラ: GitHub Actions (スケジュール実行), GitHub Pages (静的ホスティング)
- データ取得: J-Quants API (JPX 公式、無料プラン)

---

## ファイル構成

プロジェクトリポジトリの構成を先に定める（実装開始前に確認）：

```
tsea-investment-app/
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── data_ingestion/               # データ取得サービス（データエンジニア担当）
│   ├── __init__.py
│   ├── main.py                   # エントリーポイント（cronで実行）
│   ├── jquants_client.py         # J-Quants API ラッパー
│   ├── database.py               # PostgreSQL/SQLite 接続
│   └── tests/
│       └── test_jquants_client.py
│
├── analysis/                     # 分析サービス（バックエンドエンジニア担当）
│   ├── __init__.py
│   ├── main.py                   # エントリーポイント
│   ├── calculations.py           # 資金流入・パフォーマンス計算
│   ├── discord_notifier.py       # Discord webhook 送信
│   └── tests/
│       ├── test_calculations.py
│       └── test_discord_notifier.py
│
├── api/                          # REST API サービス（オプション）
│   ├── __init__.py
│   ├── main.py                   # FastAPI アプリケーション
│   ├── routes/
│   │   └── sectors.py            # /api/sectors/* エンドポイント
│   └── tests/
│       └── test_api.py
│
├── frontend/                     # React フロントエンド（フロントエンドエンジニア担当）
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.js
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SectorDetail.jsx
│   │   │   └── Charts.jsx
│   │   ├── hooks/
│   │   │   └── useData.js
│   │   ├── styles/
│   │   │   └── index.css
│   │   └── __tests__/
│   │       └── App.test.js
│   ├── package.json
│   └── .env.example
│
├── .github/
│   └── workflows/
│       ├── data-ingestion.yml    # 毎営業日 6:00 UTC 実行
│       ├── analysis.yml          # データ取得直後に実行
│       ├── frontend-deploy.yml   # フロントエンドを GitHub Pages にデプロイ
│       └── tests.yml             # 各 commit でテスト実行
│
├── sql/                          # データベーススキーマ
│   └── schema.sql
│
├── docs/
│   ├── superpowers/
│   │   ├── specs/
│   │   │   └── 2026-05-30-market-analysis-design.md
│   │   └── plans/
│   │       └── 2026-05-30-market-analysis-implementation.md
│   ├── API.md                    # API ドキュメント
│   └── SETUP.md                  # セットアップガイド
│
└── .gitignore
    .env.local
    __pycache__/
    node_modules/
    dist/
    .DS_Store
```

---

## フェーズ 1: バックエンド・データ基盤（1-2 週間）

### 全体目標
- Supabase / SQLite データベーススキーマ作成
- J-Quants API 接続確認
- データ取得スクリプト実装・テスト
- 分析計算ロジック実装・テスト
- GitHub Actions ワークフロー確認

### Task 1-1: プロジェクト初期化・環境構築

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Modify: `README.md`

**Subtasks:**

- [ ] **Step 1: requirements.txt を作成**

```txt
# Data processing
pandas==2.0.3
numpy==1.24.3

# API
requests==2.31.0
fastapi==0.104.1
uvicorn==0.24.0

# Database
psycopg2-binary==2.9.9
supabase==2.3.0
sqlalchemy==2.0.23

# Scheduling & utilities
jpbizday==0.4.1

# Discord
discord-webhook==1.1.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Frontend
Node.js 18+ (別途インストール)
```

- [ ] **Step 2: pyproject.toml を作成**

```toml
[tool.pytest.ini_options]
testpaths = ["data_ingestion/tests", "analysis/tests", "api/tests"]
addopts = "-v --cov=data_ingestion --cov=analysis --cov=api --cov-report=html"

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
```

- [ ] **Step 3: .env.example を作成**

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# J-Quants API
JQUANTS_API_KEY=your-jquants-api-key

# Discord
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# Development
DATABASE_TYPE=sqlite  # または 'supabase'
DEBUG=false
```

- [ ] **Step 4: .gitignore を作成**

```
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
.env
.env.local
node_modules/
dist/
build/
*.egg-info/
.DS_Store
venv/
```

- [ ] **Step 5: README.md を更新**

```markdown
# 東証セクター資金流入分析プラットフォーム

## セットアップ

1. リポジトリクローン
2. `pip install -r requirements.txt`
3. `.env.example` を `.env` にコピー、認証情報を入力
4. `python data_ingestion/main.py` でデータ取得テスト

詳細は `docs/SETUP.md` を参照
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt pyproject.toml .gitignore .env.example README.md
git commit -m "init: project setup with dependencies"
```

---

### Task 1-2: Supabase データベーススキーマ作成

**Files:**
- Create: `sql/schema.sql`
- Create: `data_ingestion/database.py`
- Create: `data_ingestion/tests/test_database.py`

**Subtasks:**

- [ ] **Step 1: schema.sql を作成**

```sql
-- Supabase: SQL エディタで実行
-- または psql コマンドで: psql -h db.supabase.co -U postgres -d postgres < sql/schema.sql

CREATE TABLE IF NOT EXISTS sectors (
  id SERIAL PRIMARY KEY,
  tse33_code INT UNIQUE NOT NULL,
  sector_name VARCHAR(100) UNIQUE NOT NULL,
  sector_name_en VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master_stocks (
  id SERIAL PRIMARY KEY,
  stock_code VARCHAR(4) UNIQUE NOT NULL,
  stock_name VARCHAR(255) NOT NULL,
  market_tier VARCHAR(20),
  sector_id INT REFERENCES sectors(id),
  jquants_code VARCHAR(6),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_prices (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  open_price DECIMAL(10, 2),
  high_price DECIMAL(10, 2),
  low_price DECIMAL(10, 2),
  close_price DECIMAL(10, 2),
  volume BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(stock_id, date)
);

CREATE TABLE IF NOT EXISTS daily_trading (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  trading_value_jpy BIGINT,
  vwap DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(stock_id, date)
);

CREATE TABLE IF NOT EXISTS sector_daily_aggregates (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  total_trading_value_jpy BIGINT,
  total_volume BIGINT,
  stock_count INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(date, sector_id)
);

CREATE TABLE IF NOT EXISTS sector_performance (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  perf_1d DECIMAL(5, 2),
  perf_5d DECIMAL(5, 2),
  perf_20d DECIMAL(5, 2),
  perf_60d DECIMAL(5, 2),
  vs_topix_1d DECIMAL(5, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(date, sector_id)
);

CREATE TABLE IF NOT EXISTS sector_fund_flow (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  fund_flow_amount_jpy BIGINT,
  fund_flow_rank INT,
  fund_flow_pct_change DECIMAL(5, 2),
  trend_5d VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(date, sector_id)
);

-- TSE33業種コード初期化
INSERT INTO sectors (tse33_code, sector_name) VALUES
(1, '機械・器具'),
(2, '電気・ガス業'),
(3, '情報・通信業'),
(4, '銀行業'),
(5, '証券・商品先物取引業'),
(6, '保険業'),
(7, '不動産業'),
(8, '鉱業'),
(9, '食料品'),
(10, 'エネルギー・素材'),
(11, '自動車'),
(12, '輸送用機械'),
(13, 'ゴム製品'),
(14, 'ケミカルズ'),
(15, '医薬品'),
(16, '化粧品・日用雑貨'),
(17, 'パルプ・紙'),
(18, 'セメント・建材'),
(19, 'ガラス・土石製品'),
(20, '鉄鋼'),
(21, '非鉄金属'),
(22, '金属製品'),
(23, '建設業'),
(24, '電気・ガス・水道業'),
(25, 'インターネット・販売'),
(26, 'サービス業'),
(27, '陸運業'),
(28, '海運業'),
(29, '空運業'),
(30, '倉庫・運搬関連'),
(31, '物流サービス'),
(32, '流通'),
(33, '小売業')
ON CONFLICT (tse33_code) DO NOTHING;
```

- [ ] **Step 2: database.py を作成**

```python
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
            result = conn.execute(text(query), params or {})
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
```

- [ ] **Step 3: test_database.py を作成**

```python
import pytest
import os
from data_ingestion.database import Database

@pytest.fixture
def test_db():
    """テスト用データベース"""
    os.environ['DATABASE_TYPE'] = 'sqlite'
    db = Database()
    # スキーマ初期化
    with open('sql/schema.sql', 'r') as f:
        db.execute(f.read())
    yield db
    # クリーンアップ
    os.remove('data/market.db') if os.path.exists('data/market.db') else None

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
```

- [ ] **Step 4: テスト実行**

```bash
cd data_ingestion
pytest tests/test_database.py -v
# Expected: PASSED
```

- [ ] **Step 5: Commit**

```bash
git add sql/schema.sql data_ingestion/database.py data_ingestion/tests/test_database.py
git commit -m "feat: database schema and connection layer"
```

---

### Task 1-3: J-Quants API クライアント実装

**Files:**
- Create: `data_ingestion/jquants_client.py`
- Create: `data_ingestion/tests/test_jquants_client.py`

**Subtasks:**

- [ ] **Step 1: jquants_client.py を作成**

```python
import os
import requests
from datetime import date, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class JQuantsClient:
    BASE_URL = "https://api.jquants.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })
    
    def get_stocks_info(self) -> List[Dict]:
        """
        全銘柄情報を取得
        Returns: [{'code': '1001', 'name': '...',  'sector': '01', ...}, ...]
        """
        url = f"{self.BASE_URL}/stocks"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('stocks', [])
    
    def get_daily_prices(self, date_str: str, code: Optional[str] = None) -> List[Dict]:
        """
        指定日付の株価データ取得
        Args:
            date_str: 'YYYY-MM-DD'
            code: 証券コード（省略時は全銘柄）
        Returns: [{'date': '...', 'code': '1001', 'open': ..., 'close': ..., 'volume': ...}, ...]
        """
        params = {'date': date_str}
        if code:
            params['code'] = code
        
        url = f"{self.BASE_URL}/daily_prices"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('daily_prices', [])
    
    def get_trading_values(self, date_str: str) -> List[Dict]:
        """
        売買代金データ取得
        Returns: [{'date': '...', 'code': '1001', 'trading_value': ..., 'vwap': ...}, ...]
        """
        params = {'date': date_str}
        url = f"{self.BASE_URL}/trading_values"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('trading_values', [])
    
    def get_indices(self, date_str: str, code: str = '0001') -> Optional[Dict]:
        """
        指数データ取得（TOPIX など）
        Args:
            code: '0001' = TOPIX
        Returns: {'date': '...', 'open': ..., 'close': ..., 'high': ..., 'low': ...}
        """
        params = {'date': date_str, 'code': code}
        url = f"{self.BASE_URL}/indices"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        indices = data.get('indices', [])
        return indices[0] if indices else None

class JQuantsDataFetcher:
    """データ取得オーケストレーター"""
    
    def __init__(self, api_key: str):
        self.client = JQuantsClient(api_key)
    
    def fetch_yesterday_data(self, yesterday: date) -> Dict:
        """
        昨日のデータをまとめて取得
        Returns: {'stocks': [...], 'prices': [...], 'trading_values': [...], 'topix': {...}}
        """
        date_str = yesterday.strftime('%Y-%m-%d')
        
        try:
            stocks = self.client.get_stocks_info()
            prices = self.client.get_daily_prices(date_str)
            trading = self.client.get_trading_values(date_str)
            topix = self.client.get_indices(date_str)
            
            logger.info(f"Fetched {len(prices)} stock prices for {date_str}")
            return {
                'stocks': stocks,
                'prices': prices,
                'trading_values': trading,
                'topix': topix
            }
        except requests.RequestException as e:
            logger.error(f"API error: {e}")
            raise

# グローバルインスタンス
def get_fetcher() -> JQuantsDataFetcher:
    api_key = os.getenv('JQUANTS_API_KEY')
    if not api_key:
        raise ValueError("JQUANTS_API_KEY not set")
    return JQuantsDataFetcher(api_key)
```

- [ ] **Step 2: test_jquants_client.py を作成**

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from data_ingestion.jquants_client import JQuantsClient, JQuantsDataFetcher
from datetime import date

@pytest.fixture
def mock_api():
    """Mock J-Quants API"""
    with patch('data_ingestion.jquants_client.requests.Session') as mock_session:
        yield mock_session

def test_get_stocks_info(mock_api):
    """銘柄情報取得テスト"""
    client = JQuantsClient('test-key')
    
    # Mock レスポンス
    mock_response = Mock()
    mock_response.json.return_value = {
        'stocks': [
            {'code': '1001', 'name': 'テスト太郎', 'sector': '01'},
            {'code': '1002', 'name': 'テスト花子', 'sector': '02'}
        ]
    }
    client.session.get = Mock(return_value=mock_response)
    
    # テスト実行
    stocks = client.get_stocks_info()
    
    # 確認
    assert len(stocks) == 2
    assert stocks[0]['code'] == '1001'
    client.session.get.assert_called_once()

def test_get_daily_prices(mock_api):
    """日次株価取得テスト"""
    client = JQuantsClient('test-key')
    
    mock_response = Mock()
    mock_response.json.return_value = {
        'daily_prices': [
            {
                'date': '2026-05-30',
                'code': '1001',
                'open': 100.0,
                'high': 102.0,
                'low': 99.0,
                'close': 101.0,
                'volume': 1000000
            }
        ]
    }
    client.session.get = Mock(return_value=mock_response)
    
    prices = client.get_daily_prices('2026-05-30')
    
    assert len(prices) == 1
    assert prices[0]['close'] == 101.0

def test_get_indices(mock_api):
    """TOPIX 取得テスト"""
    client = JQuantsClient('test-key')
    
    mock_response = Mock()
    mock_response.json.return_value = {
        'indices': [
            {
                'date': '2026-05-30',
                'code': '0001',
                'open': 2750.0,
                'high': 2765.0,
                'low': 2740.0,
                'close': 2760.0
            }
        ]
    }
    client.session.get = Mock(return_value=mock_response)
    
    topix = client.get_indices('2026-05-30')
    
    assert topix is not None
    assert topix['close'] == 2760.0

def test_fetch_yesterday_data():
    """日次データ一括取得テスト"""
    fetcher = JQuantsDataFetcher('test-key')
    
    # Mock
    fetcher.client.get_stocks_info = Mock(return_value=[{'code': '1001', 'name': 'テスト'}])
    fetcher.client.get_daily_prices = Mock(return_value=[{'code': '1001', 'close': 101.0}])
    fetcher.client.get_trading_values = Mock(return_value=[{'code': '1001', 'trading_value': 1000000}])
    fetcher.client.get_indices = Mock(return_value={'close': 2760.0})
    
    # テスト実行
    data = fetcher.fetch_yesterday_data(date(2026, 5, 30))
    
    # 確認
    assert 'stocks' in data
    assert 'prices' in data
    assert 'trading_values' in data
    assert 'topix' in data
    assert len(data['stocks']) == 1
```

- [ ] **Step 3: テスト実行**

```bash
cd data_ingestion
pytest tests/test_jquants_client.py -v
# Expected: PASSED
```

- [ ] **Step 4: Commit**

```bash
git add data_ingestion/jquants_client.py data_ingestion/tests/test_jquants_client.py
git commit -m "feat: J-Quants API client"
```

---

### Task 1-4: データ取得メインスクリプト実装

**Files:**
- Create: `data_ingestion/main.py`
- Create: `data_ingestion/tests/test_main.py`

**Subtasks:**

- [ ] **Step 1: main.py を作成**

```python
import os
import logging
from datetime import datetime, timedelta, timezone
import jpbizday
from data_ingestion.database import db
from data_ingestion.jquants_client import get_fetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    データ取得メインプロセス
    - 昨日が営業日か確認
    - J-Quants API から データを取得
    - Supabase / SQLite に保存
    """
    
    # Step 1: 営業日判定（祝日スキップ）
    JST = timezone(timedelta(hours=9))
    yesterday = (datetime.now(tz=JST) - timedelta(days=1)).date()
    
    if not jpbizday.isopen(yesterday):
        logger.info(f"{yesterday} is a holiday, skipping data ingestion")
        return
    
    logger.info(f"Starting data ingestion for {yesterday}")
    
    # Step 2: API からデータ取得
    try:
        fetcher = get_fetcher()
        data = fetcher.fetch_yesterday_data(yesterday)
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise
    
    # Step 3: データベース に保存
    try:
        # 銘柄マスタ挿入（初回のみ）
        stocks_to_insert = []
        for stock in data['stocks']:
            stocks_to_insert.append({
                'stock_code': stock['code'],
                'stock_name': stock.get('name', 'Unknown'),
                'market_tier': stock.get('market_tier', ''),
                'sector_id': int(stock['sector']),
                'jquants_code': stock['code']
            })
        db.insert_stocks(stocks_to_insert)
        logger.info(f"Inserted/updated {len(stocks_to_insert)} stocks")
        
        # 日次株価挿入
        prices_to_insert = []
        for price in data['prices']:
            prices_to_insert.append({
                'stock_id': None,  # 実装時に stock_code から stock_id をルックアップ
                'date': yesterday,
                'open_price': price.get('open'),
                'high_price': price.get('high'),
                'low_price': price.get('low'),
                'close_price': price.get('close'),
                'volume': price.get('volume', 0)
            })
        # TODO: stock_id ルックアップロジック追加
        # db.insert_daily_prices(prices_to_insert)
        logger.info(f"Inserted {len(prices_to_insert)} daily prices")
        
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        raise
    
    logger.info("Data ingestion completed successfully")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: test_main.py を作成**

```python
import pytest
from unittest.mock import patch, Mock
from datetime import date, datetime, timezone, timedelta
from data_ingestion.main import main

@patch('data_ingestion.main.jpbizday.isopen')
@patch('data_ingestion.main.get_fetcher')
@patch('data_ingestion.main.db')
def test_main_skips_holiday(mock_db, mock_fetcher, mock_isopen):
    """祝日スキップテスト"""
    mock_isopen.return_value = False
    
    main()
    
    # API が呼ばれないことを確認
    mock_fetcher.assert_not_called()
    mock_db.insert_stocks.assert_not_called()

@patch('data_ingestion.main.jpbizday.isopen')
@patch('data_ingestion.main.get_fetcher')
@patch('data_ingestion.main.db')
def test_main_processes_business_day(mock_db, mock_fetcher, mock_isopen):
    """営業日データ取得テスト"""
    mock_isopen.return_value = True
    
    # Mock fetcher
    mock_instance = Mock()
    mock_instance.fetch_yesterday_data.return_value = {
        'stocks': [{'code': '1001', 'name': 'テスト', 'sector': '01', 'market_tier': 'プライム'}],
        'prices': [{'code': '1001', 'open': 100.0, 'close': 101.0, 'volume': 1000000}],
        'trading_values': [],
        'topix': {}
    }
    mock_fetcher.return_value = mock_instance
    
    main()
    
    # API が呼ばれたことを確認
    mock_instance.fetch_yesterday_data.assert_called_once()
    mock_db.insert_stocks.assert_called_once()

@patch('data_ingestion.main.jpbizday.isopen')
@patch('data_ingestion.main.get_fetcher')
def test_main_handles_api_error(mock_fetcher, mock_isopen):
    """API エラーハンドリングテスト"""
    mock_isopen.return_value = True
    mock_fetcher.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        main()
```

- [ ] **Step 3: テスト実行**

```bash
cd data_ingestion
pytest tests/test_main.py -v
# Expected: PASSED
```

- [ ] **Step 4: 手動実行テスト**

```bash
export JQUANTS_API_KEY="your-test-key"
python -m data_ingestion.main
# Expected: "Data ingestion completed successfully" または祝日スキップメッセージ
```

- [ ] **Step 5: Commit**

```bash
git add data_ingestion/main.py data_ingestion/tests/test_main.py
git commit -m "feat: data ingestion main script"
```

---

### Task 1-5: 分析計算エンジン実装

**Files:**
- Create: `analysis/calculations.py`
- Create: `analysis/tests/test_calculations.py`

**Subtasks:**

- [ ] **Step 1: calculations.py を作成**

```python
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional
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
        Args:
            trading_values: {'sector_name': trading_value_jpy}
            performance_pct: {'sector_name': pct_change}
        Returns: {'sector_name': fund_flow_score}
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
    ) -> Dict[str, float]:
        """
        セクター別パフォーマンス計算
        Args:
            daily_prices: {'sector': [...], 'close': [...], 'date': [...]}
            window_days: 計算期間（営業日）
        Returns: {'sector': performance_pct}
        """
        performance = {}
        
        for sector in daily_prices['sector'].unique():
            sector_data = daily_prices[daily_prices['sector'] == sector].sort_values('date')
            
            if len(sector_data) < window_days:
                # データ不足の場合は NULL
                performance[sector] = None
            else:
                start_price = sector_data.iloc[-window_days]['close']
                end_price = sector_data.iloc[-1]['close']
                pct_change = ((end_price - start_price) / start_price) * 100
                performance[sector] = round(pct_change, 2)
        
        return performance
    
    @staticmethod
    def calculate_vs_topix(
        sector_performance: Dict[str, float],
        topix_performance: float
    ) -> Dict[str, float]:
        """
        TOPIX 比パフォーマンス計算
        Returns: {'sector': vs_topix_pct}
        """
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
        Returns: {'sector': rank (1が最高)}
        """
        sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {sector: i + 1 for i, (sector, _) in enumerate(sorted_sectors)}

class PerformanceCalculator:
    """パフォーマンス計算（単一セクター）"""
    
    @staticmethod
    def calculate_daily_change(open_price: float, close_price: float) -> float:
        """1 日の騰落率計算"""
        if open_price == 0:
            return 0.0
        return ((close_price - open_price) / open_price) * 100
    
    @staticmethod
    def calculate_cumulative_return(
        prices: List[float],
        days: int
    ) -> Optional[float]:
        """累積リターン計算"""
        if len(prices) < days:
            return None
        return ((prices[-1] - prices[-days]) / prices[-days]) * 100 if prices[-days] != 0 else None

# テスト用ダミーデータ
DUMMY_SECTOR_DATA = {
    'テクノロジー': {'trading_value': 5000000000, 'perf_1d': 2.5, 'perf_5d': 1.8},
    '金融': {'trading_value': 3000000000, 'perf_1d': -1.2, 'perf_5d': 0.5},
    'エネルギー': {'trading_value': 2000000000, 'perf_1d': 1.0, 'perf_5d': -0.3}
}
```

- [ ] **Step 2: test_calculations.py を作成**

```python
import pytest
from analysis.calculations import SectorAnalyzer, PerformanceCalculator
import pandas as pd

class TestSectorAnalyzer:
    
    def test_calculate_fund_flow_score(self):
        """資金流入スコア計算テスト"""
        trading_values = {
            'テクノロジー': 5000000000,
            '金融': 3000000000
        }
        performance_pct = {
            'テクノロジー': 2.5,  # 上昇
            '金融': -1.2  # 下落
        }
        
        scores = SectorAnalyzer.calculate_fund_flow_score(trading_values, performance_pct)
        
        # テクノロジーは正のスコア、金融は負のスコア
        assert scores['テクノロジー'] == 5000000000
        assert scores['金融'] == -3000000000
    
    def test_calculate_sector_performance(self):
        """セクター別パフォーマンス計算テスト"""
        data = pd.DataFrame({
            'sector': ['テクノロジー'] * 5,
            'close': [100.0, 101.0, 102.0, 103.0, 104.0],
            'date': pd.date_range('2026-05-26', periods=5)
        })
        
        perf = SectorAnalyzer.calculate_sector_performance(data, window_days=5)
        
        # 5日間で 100 → 104, つまり 4% 上昇
        assert perf['テクノロジー'] == pytest.approx(4.0, abs=0.01)
    
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

class TestPerformanceCalculator:
    
    def test_calculate_daily_change(self):
        """1 日騰落率テスト"""
        change = PerformanceCalculator.calculate_daily_change(100.0, 102.0)
        assert change == pytest.approx(2.0, abs=0.01)
    
    def test_calculate_cumulative_return(self):
        """累積リターン計算テスト"""
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        return_5d = PerformanceCalculator.calculate_cumulative_return(prices, 5)
        assert return_5d == pytest.approx(4.0, abs=0.01)
    
    def test_insufficient_data(self):
        """データ不足テスト"""
        prices = [100.0, 101.0]
        return_5d = PerformanceCalculator.calculate_cumulative_return(prices, 5)
        assert return_5d is None
```

- [ ] **Step 3: テスト実行**

```bash
cd analysis
pytest tests/test_calculations.py -v
# Expected: PASSED
```

- [ ] **Step 4: Commit**

```bash
git add analysis/calculations.py analysis/tests/test_calculations.py
git commit -m "feat: sector analysis calculations"
```

---

### Task 1-6: 分析メインスクリプト実装

**Files:**
- Create: `analysis/main.py`
- Create: `analysis/discord_notifier.py`
- Create: `analysis/tests/test_main.py`

**Subtasks:**

- [ ] **Step 1: discord_notifier.py を作成**

```python
import os
import logging
from typing import Dict, List
from datetime import date
from discord_webhook import DiscordWebhook

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord メッセージ送信"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_daily_summary(
        self,
        analysis_date: date,
        top_inflow_sectors: List[Dict],
        top_outflow_sectors: List[Dict],
        performance_changes: Dict
    ):
        """
        日次分析結果を Discord に投稿
        Args:
            analysis_date: 分析日付
            top_inflow_sectors: [{'sector': 'テクノロジー', 'score': ...}, ...]
            top_outflow_sectors: [{'sector': '金融', 'score': ...}, ...]
            performance_changes: {'1d': {...}, '5d': {...}}
        """
        
        # メッセージ本文作成
        message = f"📊 **セクター市場分析 — {analysis_date}**\n\n"
        
        # 流入セクター Top 5
        message += "**💰 資金流入上位 5 セクター:**\n"
        for i, sector_data in enumerate(top_inflow_sectors[:5], 1):
            score = sector_data['score'] / 1e9  # 十億単位
            message += f"{i}. {sector_data['sector']}: ¥{score:.1f}B\n"
        message += "\n"
        
        # 流出セクター Top 5
        message += "**📉 資金流出上位 5 セクター:**\n"
        for i, sector_data in enumerate(top_outflow_sectors[:5], 1):
            score = abs(sector_data['score']) / 1e9
            message += f"{i}. {sector_data['sector']}: -¥{score:.1f}B\n"
        message += "\n"
        
        # パフォーマンス変動
        message += "**📈 パフォーマンス変動（1 日）:**\n"
        top_performers = sorted(
            performance_changes.get('1d', {}).items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for sector, perf in top_performers:
            message += f"- {sector}: {perf:+.2f}%\n"
        
        message += f"\n🔗 詳細分析: [ダッシュボード](https://your-github-pages-url)\n"
        
        # 送信
        webhook = DiscordWebhook(url=self.webhook_url, content=message)
        try:
            webhook.execute()
            logger.info(f"Discord notification sent for {analysis_date}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise
```

- [ ] **Step 2: analysis/main.py を作成**

```python
import os
import logging
from datetime import datetime, timedelta, timezone, date
from analysis.calculations import SectorAnalyzer
from analysis.discord_notifier import DiscordNotifier
from data_ingestion.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    分析メインプロセス
    - データベースから昨日のデータを読み込み
    - セクター別に集計・計算
    - 結果を保存
    - Discord に通知
    """
    
    # 分析対象日（昨日）
    JST = timezone(timedelta(hours=9))
    analysis_date = (datetime.now(tz=JST) - timedelta(days=1)).date()
    
    logger.info(f"Starting analysis for {analysis_date}")
    
    try:
        # Step 1: データ取得
        # TODO: database から daily_prices, daily_trading を読み込み
        
        # Step 2: セクター別集計
        # TODO: 売買代金、騰落率を計算
        
        # Step 3: ランキング計算
        # TODO: SectorAnalyzer を使用してランキング生成
        
        # Step 4: 結果をデータベースに保存
        # TODO: sector_daily_aggregates, sector_performance に insert
        
        # Step 5: Discord 通知送信
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        if webhook_url:
            notifier = DiscordNotifier(webhook_url)
            # TODO: top_inflow_sectors, top_outflow_sectors を組立
            # notifier.send_daily_summary(analysis_date, top_inflow_sectors, ...)
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: test_main.py を作成（分析用）**

```python
import pytest
from unittest.mock import Mock, patch
from analysis.discord_notifier import DiscordNotifier

def test_discord_notification():
    """Discord 通知テスト"""
    notifier = DiscordNotifier('https://dummy-webhook-url')
    
    with patch('analysis.discord_notifier.DiscordWebhook') as mock_webhook:
        mock_instance = Mock()
        mock_webhook.return_value = mock_instance
        
        notifier.send_daily_summary(
            analysis_date='2026-05-30',
            top_inflow_sectors=[
                {'sector': 'テクノロジー', 'score': 5000000000},
                {'sector': 'ヘルスケア', 'score': 3000000000}
            ],
            top_outflow_sectors=[
                {'sector': '金融', 'score': -2000000000}
            ],
            performance_changes={'1d': {'テクノロジー': 2.5}}
        )
        
        mock_instance.execute.assert_called_once()
```

- [ ] **Step 4: テスト実行**

```bash
pytest analysis/tests/test_main.py -v
# Expected: PASSED
```

- [ ] **Step 5: Commit**

```bash
git add analysis/main.py analysis/discord_notifier.py analysis/tests/test_main.py
git commit -m "feat: analysis engine and Discord notifier"
```

---

## フェーズ 2: API・Discord 連携（1 週間）

[後続セクションで続行 - スペース制限のため省略]

## フェーズ 3: フロントエンド（1 週間）

[後続セクションで続行]

## フェーズ 4: テスト・リリース（1 週間）

[後続セクションで続行]

---

## 役割分担マトリックス

| タスク | データエンジ | バックエンド | フロントエンド |
|--------|-----------|----------|----------|
| 1-1: 初期化 | ✓ | ✓ | ✓ |
| 1-2: DB スキーマ | ✓ | ✓ | - |
| 1-3: J-Quants | ✓ | - | - |
| 1-4: データ取得 | ✓ | ✓ | - |
| 1-5: 計算エンジン | ✓ | ✓ | - |
| 1-6: 分析・Discord | - | ✓ | - |
| 2-x: API | - | ✓ | - |
| 2-x: GitHub Actions | ✓ | ✓ | - |
| 3-x: React Dashboard | - | - | ✓ |
| 4-x: テスト | ✓ | ✓ | ✓ |

---

## リスク・緩和策

| リスク | 発生時期 | 緩和策 |
|--------|---------|--------|
| J-Quants API 無料プランの 12 週間制限 | フェーズ 1 | perf_60d は NULL で運用開始、後で有料化 |
| Supabase 無料枠 7 日無アクセスで停止 | 本番運用 | GitHub Actions が毎日実行するため無影響 |
| 臨時休場対応 (jpbizday 非対応) | フェーズ 1 | 手動確認または JPX カレンダー同期スクリプト追加 |
| TSE33 コード変更 | フェーズ 1 | 初期化スクリプトで定期更新可能 |

---

## テスト戦略

**ユニットテスト:**
- 計算ロジック（資金流入スコア、パフォーマンス） → `analysis/tests/`
- API クライアント → `data_ingestion/tests/`
- DB 層 → テスト用 SQLite 使用

**統合テスト:**
- データ取得 → DB 保存 → 分析計算 → 結果確認

**E2E テスト:**
- GitHub Actions ワークフロー実行 → 結果確認

**カバレッジ目標:** >= 80%

---

## 次のステップ

本計画の詳細タスク（フェーズ 2-4）は別途提供します。

実装開始前に：
1. Supabase アカウント作成・プロジェクト初期化
2. J-Quants API キー取得
3. Discord webhook URL 作成
4. GitHub Actions secrets 設定（SUPABASE_URL, SUPABASE_KEY, JQUANTS_API_KEY, DISCORD_WEBHOOK）
5. リポジトリのプロテクテッドブランチ設定（main）
