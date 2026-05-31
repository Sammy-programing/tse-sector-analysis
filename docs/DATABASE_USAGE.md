# データベース使用状況レポート

## 現在のデータベーススキーマ

### テーブル一覧と目的

| テーブル | 目的 | 記録内容 | 現在の使用状況 |
|---------|------|--------|-------------|
| **sectors** | セクターマスタ | 33業種のセクター情報 | ✅ 初期化のみ、分析時は参照 |
| **master_stocks** | 銘柄マスタ | 全銘柄コード、名前、セクター | ⚠️ 取得できるが使用未実装 |
| **daily_prices** | 日次株価 | 始値・終値・出来高 | ⚠️ 取得予定、未使用 |
| **daily_trading** | 日次売買代金 | 売買代金、VWAP | ⚠️ 取得予定、未使用 |
| **sector_daily_aggregates** | セクター集計 | セクター別の売買代金合計 | ⚠️ 構造のみ、未使用 |
| **sector_performance** | セクターパフォーマンス | 1d/5d/20d/60d リターン | ⚠️ 構造のみ、未使用 |
| **sector_fund_flow** | セクター資金流入 | 資金流入量・ランク・トレンド | ⚠️ 構造のみ、未使用 |

---

## 現在のデータフロー

```
J-Quants API
  ↓
jquants_client.py (取得)
  ├── get_stocks_info() → 銘柄一覧
  ├── get_daily_prices() → 日次価格
  ├── get_trading_values() → 売買代金
  └── get_indices() → 指数データ
  ↓
database.py (保存)
  ├── insert_stocks() → master_stocks テーブル
  ├── insert_daily_prices() → daily_prices テーブル
  ├── insert_daily_trading() → daily_trading テーブル
  └── insert_sector_* → セクター関連テーブル
  ↓
API エンドポイント
  ├── /api/sectors/fund-flow → ダミーデータ返却 (TODO)
  ├── /api/sectors/performance → ダミーデータ返却 (TODO)
  └── /api/sectors/{id}/history → 未実装
```

---

## 各テーブルの詳細

### 1. sectors テーブル
```sql
CREATE TABLE sectors (
  id SERIAL PRIMARY KEY,
  tse33_code INT UNIQUE,        -- TSE33業種コード (1-33)
  sector_name VARCHAR(100),      -- 日本語セクター名
  sector_name_en VARCHAR(100),   -- 英語セクター名
  created_at TIMESTAMP
);
```

**利用パターン:**
- セクター ID → セクター名の変換
- セクター分析時の参照
- 現在: 初期化のみ（33行の初期データ）

---

### 2. master_stocks テーブル
```sql
CREATE TABLE master_stocks (
  id SERIAL PRIMARY KEY,
  stock_code VARCHAR(4) UNIQUE,  -- 証券コード例: "7203"
  stock_name VARCHAR(255),        -- トヨタ自動車 など
  market_tier VARCHAR(20),        -- プライム/スタンダード など
  sector_id INT REFERENCES sectors(id),
  jquants_code VARCHAR(6),        -- J-Quants API用コード
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**利用パターン:**
- stock_code → stock_id の変換（外部キーとして利用）
- 銘柄名の取得
- セクター別銘柄抽出
- 現在: 取得コード実装済み（database.py に `insert_stocks()`, `get_stock_id_by_code()`, `get_all_stocks()`）
- しかし API では使用されていない

---

### 3. daily_prices テーブル
```sql
CREATE TABLE daily_prices (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  open_price DECIMAL(10, 2),
  high_price DECIMAL(10, 2),
  low_price DECIMAL(10, 2),
  close_price DECIMAL(10, 2),
  volume BIGINT,
  created_at TIMESTAMP,
  UNIQUE(stock_id, date)
);
```

**利用パターン:**
- 日次株価の永続化
- テクニカル分析（移動平均など）
- パフォーマンス計算
- 現在: 取得・保存は実装予定、実際には使用されていない

---

### 4. daily_trading テーブル
```sql
CREATE TABLE daily_trading (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  trading_value_jpy BIGINT,      -- 売買代金（円）
  vwap DECIMAL(10, 2),           -- Volume Weighted Average Price
  created_at TIMESTAMP,
  UNIQUE(stock_id, date)
);
```

**利用パターン:**
- 売買代金ランキング（銘柄）
- 流動性判定
- 買い時判定
- 現在: 未実装

---

### 5. sector_daily_aggregates テーブル
```sql
CREATE TABLE sector_daily_aggregates (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  total_trading_value_jpy BIGINT,
  total_volume BIGINT,
  stock_count INT,
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);
```

**目的:**
- セクター別の集計統計
- 構造は存在するが未使用

---

### 6. sector_performance テーブル
```sql
CREATE TABLE sector_performance (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  perf_1d DECIMAL(5, 2),         -- 1日リターン（%）
  perf_5d DECIMAL(5, 2),
  perf_20d DECIMAL(5, 2),
  perf_60d DECIMAL(5, 2),
  vs_topix_1d DECIMAL(5, 2),     -- TOPIX相対パフォーマンス
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);
```

**目的:**
- セクター別パフォーマンス履歴保存
- 構造は存在するが未使用

---

### 7. sector_fund_flow テーブル
```sql
CREATE TABLE sector_fund_flow (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  fund_flow_amount_jpy BIGINT,
  fund_flow_rank INT,
  fund_flow_pct_change DECIMAL(5, 2),
  trend_5d VARCHAR(20),
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);
```

**目的:**
- セクター別資金流入度ランキング
- トレンド記録
- 構造は存在するが未使用

---

## 現在の実装ギャップ

| 機能 | 予定 | 実装 | 使用 |
|-----|------|------|------|
| J-Quants データ取得 | ✅ | ✅ | ⚠️（分析層で未使用） |
| Supabase 接続 | ✅ | ✅ | ⚠️（テスト対応のみ） |
| 銘柄マスタ保存 | ✅ | ✅ | ❌ |
| 日次株価保存 | ✅ | ✅ | ❌ |
| 売買代金保存 | ✅ | ✅ | ❌ |
| API エンドポイント | ✅ | ✅ | ❌（ダミーデータ） |
| セクター分析 | ✅ | ✅ | ❌（Discord 通知未） |
| 銘柄分析 | ❌ | ❌ | ❌ |

---

## データベースの実際の状態

### Supabase 接続テスト

```python
# 接続確認コマンド
from data_ingestion.database import Database

db = Database()
stocks = db.get_all_stocks()
print(f"Database has {len(stocks)} stocks")
```

### 現在のテストデータ

- **sectors**: 33 行（初期化済み）
- **master_stocks**: テスト時に動的に作成
- **daily_prices**: テスト時に動的に作成
- **daily_trading**: テスト時に動的に作成
- **その他テーブル**: 本番データなし

---

## Phase 4（Discord インタラクティブ機能）で必要なデータ

### 銘柄分析に必要なデータ

```
SELECT 
  ms.stock_code,
  ms.stock_name,
  s.sector_name,
  MAX(dp.close_price) FILTER (WHERE dp.date = today) as latest_price,
  dp.close_price / LAG(dp.close_price) OVER (ORDER BY dp.date) - 1 as perf_1d,
  dt.trading_value_jpy,
  dt.vwap
FROM master_stocks ms
JOIN sectors s ON ms.sector_id = s.id
LEFT JOIN daily_prices dp ON ms.id = dp.stock_id
LEFT JOIN daily_trading dt ON ms.id = dt.stock_id
WHERE dp.date = today OR dt.date = today
ORDER BY dt.trading_value_jpy DESC
LIMIT 10;
```

### 必要なカラム（追加が必要）

現在のスキーマでは以下が不足：

| データ | 必要性 | 現在 |
|-------|-------|------|
| PER（株価収益率） | 📊 銘柄スクリーニング | ❌ なし |
| 配当利回り | 📊 銘柄スクリーニング | ❌ なし |
| 売上高 | 📊 銘柄スクリーニング | ❌ なし |
| 時価総額 | 📊 銘柄スクリーニング | ❌ なし |

---

## 実装推奨順序

### Step 1: 現在のデータ構造を有効化
- [ ] API エンドポイントをデータベースに接続
- [ ] テスト環境で daily_prices / daily_trading を保存・読み込み

### Step 2: 銘柄分析データを取得
- [ ] J-Quants から銘柄別 PER、配当などを取得
- [ ] master_stocks に追加カラム追加（または finance_metrics テーブル新規作成）

### Step 3: Discord インタラクティブ機能（Phase 4）
- [ ] 銘柄別分析エンジン実装
- [ ] Discord Bot リスナー実装
- [ ] メッセージ Formatter

---

## 推奨: 新規テーブル追加

銘柄の詳細情報を保存する場合：

```sql
CREATE TABLE stock_financial_metrics (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  per DECIMAL(10, 2),            -- 株価収益率
  dividend_yield DECIMAL(5, 2),  -- 配当利回り
  market_cap_jpy BIGINT,         -- 時価総額
  revenue_jpy BIGINT,            -- 売上高
  created_at TIMESTAMP,
  UNIQUE(stock_id, date)
);
```

---

## 結論

**現在の状態:**
- データベース構造は 7 テーブル完備
- データ取得・保存コードは実装済み
- しかし API・分析層では実際に使用されていない（ダミーデータ）
- 銘柄レベルの分析データ（PER、配当など）は未保存

**Phase 4（Discord インタラクティブ機能）実装前に:**
1. 現在のテーブルを実際に使用するよう API を修正
2. 銘柄の詳細メトリクス取得・保存を実装
3. その上で Discord Bot を実装

推奨: Step 1 → Step 2 → Phase 4 の順で実装
