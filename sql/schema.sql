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
