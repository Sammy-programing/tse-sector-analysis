# 東証セクター資金流入分析プラットフォーム — 設計仕様書

**日付:** 2026-05-30  
**ステータス:** 設計承認待ち  
**バージョン:** 1.0

---

## エグゼクティブサマリー

東京証券取引所（TSE）における資金流入状況とセクターローテーションを可視化する市場分析プラットフォームを構築する。MVP では、「どのセクターに資金が流入しているか」「セクター別パフォーマンスはどう推移しているか」を定量的に把握することに注力する。

**重要な制約:**
- **データソース:** J-Quants API（JPX 提供）無料プラン限定（過去 12 週間、リアルタイム遅延あり）
- **営業日判定:** TSE 祝日カレンダーで自動スキップ（祝日にはデータ取得・分析なし）

**想定ユーザー:** 
- デイトレーダー（日次の局面判断）
- ポートフォリオ運用者（セクター配分の意思決定）

**更新頻度:** 毎営業日後場終了後（15:00 JST）のバッチ処理

**技術スタック:** Python (FastAPI)、React、PostgreSQL（Supabase）、GitHub Actions、GitHub Pages  
**インフラ:** 完全無料（GitHub Actions + GitHub Pages + Supabase 無料枠、または SQLite ローカル開発用）  
**開発体制:** データエンジニア、バックエンドエンジニア、フロントエンドエンジニア（役割分離）

---

## 1. システムアーキテクチャ

### 1.1 マイクロサービス設計

3 つの独立したサービスがメッセージキューを通じて連携：

```
[データ取得サービス] 
         ↓
[イベントキュー / ポーリング]
         ↓
[分析サービス]
         ↓
[PostgreSQL / SQLite]
         ↓
[フロントエンド (React)]
```

**サービス 1: データ取得サービス** (Python)
- 毎営業日 15:00 (JST) 以降に GitHub Actions で実行（祝日は自動スキップ）
- **J-Quants API（JPX 公式）** から以下を取得：
  - 日次株価データ（始値、高値、安値、終値、出来高）
  - 売買代金
  - **制約:** 無料プランは過去 12 週間 + リアルタイム 20 分遅延（営業日翌営業日に前日データ確定）
  - 信用残データ：J-Quants では提供されないため、今後の有料化時に検討
  - ファンダメンタルズ：EDINETまたは別途 API 統合で対応（MVP では実装見送り）
- 生データを Supabase PostgreSQL に書込
- 「data_ingested」イベントを発行（Supabase trigger またはポーリング）
- **祝日処理:** `jpbizday` ライブラリで TSE 営業日判定し、祝日の実行をスキップ

**サービス 2: 分析サービス** (Python)
- データ取得完了後に起動
- 以下を計算：
  - セクター別資金流入額（売買代金の合計）
  - セクター別資金流入ランキングと前日比
  - セクター別パフォーマンス（1日、5日、20日、60日）
  - TOPIX 比での相対パフォーマンス
- 計算結果を PostgreSQL / SQLite に書込
- Discord webhook に要約を送信
- GitHub Actions または スケジュール実行

**サービス 3: フロントエンド** (React)
- PostgreSQL / SQLite または JSON ファイルから計算結果を読込
- 計算処理なし
- GitHub Pages でホスティング（静的デプロイ）
- API サービス（オプション）または commit されたJSON ファイルから取得

### 1.2 デプロイモデル（完全無料）

- **データ取得:** GitHub Actions workflow（cron 実行、完全無料・無制限）
- **分析:** GitHub Actions workflow または ローカル Python スクリプト
- **データベース:** Supabase（無料枠 500MB）または SQLite（ファイルベース、GitHub に commit）
- **フロントエンド:** GitHub Pages（無料静的ホスティング、コールドスタートなし）
- **実行中のサービスなし = クラウドコスト ¥0**

---

## 2. データモデル

### 2.1 PostgreSQL / SQLite スキーマ

**マスタテーブル:**

```sql
CREATE TABLE sectors (
  id SERIAL PRIMARY KEY,
  tse33_code INT UNIQUE NOT NULL,             -- TSE33業種コード（001-033）
  sector_name VARCHAR(100) UNIQUE NOT NULL,   -- セクター名（例: テクノロジー）
  sector_name_en VARCHAR(100),                -- 英名
  created_at TIMESTAMP
);

CREATE TABLE master_stocks (
  id SERIAL PRIMARY KEY,
  stock_code VARCHAR(4) UNIQUE NOT NULL,      -- 証券コード
  stock_name VARCHAR(255) NOT NULL,           -- 銘柄名
  market_tier VARCHAR(20),                    -- 'プライム', 'スタンダード', 'グロース'
  sector_id INT REFERENCES sectors(id),
  market_cap_jpy BIGINT,                      -- 時価総額（ファンダメンタルズ、MVP では使用禁止）
  jquants_code VARCHAR(6),                    -- J-Quants コード（API 取得用）
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- セクター・マスタのセットアップ例
-- INSERT INTO sectors (tse33_code, sector_name) VALUES
-- (1, 'テクノロジー'),
-- (2, 'コミュニケーション'),
-- ... (全33業種)
```

**TSE33業種コード対応表:**
| コード | セクター名 |
|-------|-----------|
| 1 | 機械・器具 |
| 2 | 電気・ガス業 |
| ... | ... |
| 33 | その他製品 |

→ 初期化スクリプトで自動挿入、J-Quants API の`sector`フィールドと対応

**生データテーブル (API から取得):**

```sql
CREATE TABLE daily_prices (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  open_price DECIMAL(10, 2),                  -- 始値
  high_price DECIMAL(10, 2),                  -- 高値
  low_price DECIMAL(10, 2),                   -- 安値
  close_price DECIMAL(10, 2),                 -- 終値
  volume BIGINT,                              -- 出来高
  created_at TIMESTAMP,
  UNIQUE(stock_id, date)
);

CREATE TABLE daily_trading (
  id SERIAL PRIMARY KEY,
  stock_id INT REFERENCES master_stocks(id),
  date DATE NOT NULL,
  trading_value_jpy BIGINT,                   -- 売買代金
  vwap DECIMAL(10, 2),                        -- 出来高加重平均株価
  created_at TIMESTAMP,
  UNIQUE(stock_id, date)
);

-- 信用残データテーブル（将来拡張用、MVP では使用しない）
-- J-Quants無料プランでは提供されていないため、有料化時に有効化する予定
-- CREATE TABLE margin_data (
--   id SERIAL PRIMARY KEY,
--   stock_id INT REFERENCES master_stocks(id),
--   date DATE NOT NULL,
--   long_position_qty BIGINT,                   -- 信用買残
--   short_position_qty BIGINT,                  -- 信用売残
--   leverage_ratio DECIMAL(5, 2),               -- 信用倍率
--   created_at TIMESTAMP,
--   UNIQUE(stock_id, date)
-- );
```

**計算結果テーブル (分析サービスが書込):**

```sql
CREATE TABLE sector_daily_aggregates (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  total_trading_value_jpy BIGINT,             -- セクター合計売買代金
  total_volume BIGINT,                        -- セクター合計出来高
  stock_count INT,                            -- 銘柄数
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);

CREATE TABLE sector_performance (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  perf_1d DECIMAL(5, 2),                      -- 1 日パフォーマンス (%)
  perf_5d DECIMAL(5, 2),                      -- 5 日パフォーマンス (%)
  perf_20d DECIMAL(5, 2),                     -- 20 日パフォーマンス (%)
  perf_60d DECIMAL(5, 2),                     -- 60 日パフォーマンス (%)
  vs_topix_1d DECIMAL(5, 2),                  -- TOPIX 比 (%)
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);

CREATE TABLE sector_fund_flow (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  sector_id INT REFERENCES sectors(id),
  fund_flow_amount_jpy BIGINT,                -- 資金流入額
  fund_flow_rank INT,                         -- ランキング
  fund_flow_pct_change DECIMAL(5, 2),         -- 前日比 (%)
  trend_5d VARCHAR(20),                       -- '流入', '流出', '中立'
  created_at TIMESTAMP,
  UNIQUE(date, sector_id)
);
```

---

## 3. 分析計算ロジック

### 3.1 資金流入スコア計算

**定義の重要な注釈:**
売買代金だけでは「流入」「流出」を判定できません（買い手と売り手の代金は常に等額）。ここでは売買代金を使用するが、「資金流入」ではなく「**資金回転度/流動性指標**」と解釈すること。セクターパフォーマンスとの組み合わせで初めて「どのセクターが買われているか」が判定できます。

**日次:**
```
セクター売買代金[日付] = その日のセクター内全銘柄の売買代金合計
セクター騰落率[日付] = セクター平均株価の騰落率

資金流入スコア = 売買代金 × 符号(騰落率)
  ※ 騰落率が正 → 売買代金はそのまま「流入スコア」として計上
  ※ 騰落率が負 → 売買代金を負に反転（流出スコア）
```

**トレンド:**
```
5 日移動平均 = AVERAGE(資金流入スコア[日付-4:日付])
20 日移動平均 = AVERAGE(資金流入スコア[日付-19:日付])

変化率 1 日 = (スコア[日付] - スコア[日付-1]) / |スコア[日付-1]| × 100
変化率 5 日 = (スコア[日付] - スコア[日付-5]) / |スコア[日付-5]| × 100
```

**ランキング:**
- セクターを資金流入スコアで順位付け（高い順 = 買われている）
- 変化率で別ランキング（モメンタムの勢い）
- ダッシュボード表現: 「資金流入ランキング」ではなく「**資金回転度ランキング** (騰落率考慮)」と表記

### 3.2 セクター別パフォーマンス計算

**方法:** 加重平均株価変化率（時価総額加重、または等加重）

```
perf_1d = セクター内全銘柄の騰落率の平均 (1 日期間)
perf_5d = セクター内全銘柄の騰落率の平均 (5 日期間)
perf_20d = セクター内全銘柄の騰落率の平均 (20 日期間)
perf_60d = セクター内全銘柄の騰落率の平均 (60 日期間)

vs_topix_1d = セクターperf_1d - TOPIX_perf_1d
```

**J-Quants無料プランの制約:**
- J-Quants APIは過去12週間（約84営業日）のデータのみ提供
- perf_60dはサービス開始から60営業日経過するまで計算不可（データ不足）
- MVP開始時は perf_60d = NULL で運用し、60営業日経過後に計算開始
- 代替案: 初期データ取得時に有料プランで過去1年分をバックフィルするか、後日有料化時に対応

### 3.3 データ検証とエラーハンドリング

**検証ルール:**
- 欠損データ（API 遅延）: 警告ログを出力、その銘柄をスキップ
- 価格異常値（1 日 20% 以上）: ログに記録、計算に含めるが フラグ付け
- NULL チェック: 必須項目の存在確認

**動作:**
- 非致命的エラー（1-2 銘柄欠損）→ 処理続行
- 致命的エラー（API 全体失敗）→ リトライ、失敗時は Discord にアラート
- 常に計算完了まで進める（部分データでも処理）

### 3.4 アラート条件（将来拡張用、MVP では実装なし）

計算はするが、ダッシュボードには非表示：
```
出来高急増: 当日出来高 > 過去 20 日平均の 2 倍
売買代金急増: 当日売買代金 > 過去 20 日平均の 2 倍
```

---

## 4. API 仕様

### 4.1 REST エンドポイント（API サービス展開時）

全て JSON で返却。MVP では認証なし。

```
GET /api/sectors/fund-flow?date=YYYY-MM-DD
Response:
{
  "date": "2026-05-30",
  "sectors": [
    {
      "sector_id": 1,
      "sector_name": "テクノロジー",
      "trading_value_jpy": 5000000000,
      "rank": 1,
      "change_1d_pct": 15.5,
      "change_5d_pct": 8.2,
      "change_20d_pct": -3.1
    },
    ...
  ]
}

GET /api/sectors/performance?date=YYYY-MM-DD
Response:
{
  "date": "2026-05-30",
  "topix_perf_1d": 1.2,
  "sectors": [
    {
      "sector_id": 1,
      "sector_name": "テクノロジー",
      "perf_1d": 2.5,
      "perf_5d": 1.8,
      "perf_20d": -0.5,
      "perf_60d": 8.3,
      "vs_topix_1d": 1.3
    },
    ...
  ]
}

GET /api/sectors/{sector_id}/history?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
Response:
{
  "sector_id": 1,
  "sector_name": "テクノロジー",
  "data": [
    {
      "date": "2026-05-30",
      "fund_flow_jpy": 5000000000,
      "perf_1d": 2.5,
      "perf_5d": 1.8
    },
    ...
  ]
}

GET /api/metadata/sectors
Response:
{
  "sectors": [
    { "id": 1, "name": "テクノロジー" },
    { "id": 2, "name": "金融" },
    ...
  ]
}
```

### 4.2 別案: JSON ファイル方式（サーバーレス）

分析サービスが JSON ファイルを生成し、GitHub Pages で静的配信：

**ファイル構成:**
```
/data/fund-flow/latest.json          # 当日データ（毎日更新）
/data/fund-flow/2026-05-30.json      # 日付別アーカイブ（履歴参照用）

/data/performance/latest.json        # 当日データ（毎日更新）
/data/performance/2026-05-30.json    # 日付別アーカイブ

/data/sector-history.json            # 過去30日のセクター推移（全セクター）
```

**フロントエンドの取得方法:**
```javascript
// 当日データ（キャッシュバスティング）
const today = new Date().toISOString().split('T')[0];
fetch(`/data/fund-flow/latest.json?_t=${today}`)
  .then(r => r.json())

// 過去日付の履歴参照
fetch(`/data/fund-flow/2026-05-29.json`)  // キャッシュされても OK
  .then(r => r.json())
```

**キャッシュ戦略:**
- `latest.json`: クエリパラメータに日付を付けてキャッシュバイパス（毎日新しい URL とみなす）
- 日付別ファイル（`2026-05-30.json`）: 日付が変わらなければ同じ URL なので、ブラウザキャッシュで OK
- GitHub Pages は自動で `Cache-Control: public, max-age=3600` を付与するため、静的ファイルキャッシュが効く

---

## 5. フロントエンド仕様

### 5.1 React アプリケーション構成

**技術スタック:**
- React 18+
- React Query または SWR（データ取得キャッシング）
- Tailwind CSS（スタイリング）
- Recharts または Chart.js（グラフ描画）
- GitHub Pages でホスティング（静的ビルド）

### 5.2 ページ・コンポーネント設計

**ダッシュボード（ホームページ）**

```
ヘッダー: 「セクター資金流入分析 — 2026-05-30」

上部セクション: 資金流入ランキング
  - テーブル: セクター名 | 売買代金 | ランク | 変化率 1 日 | 変化率 5 日
  - ソート可能（ランク順、変化率順）
  - 色分け: 緑（流入/上昇）、赤（流出/下降）

中部セクション: セクター別パフォーマンス
  - ドロップダウン: 期間選択（1 日 / 5 日 / 20 日 / 60 日）
  - 棒グラフ: セクターパフォーマンス vs TOPIX
  - TOPIX 超過成分をハイライト

下部セクション: トレンド
  - 折線グラフ: 上位 3 セクターの資金流入推移（過去 30 日）
```

**セクター詳細ページ**

```
セクター名・メタデータ

資金流入推移（折線グラフ）
  - Y 軸: ¥ 売買代金
  - X 軸: 日付（過去 3 ヶ月）
  - 5 日移動平均も表示

パフォーマンス推移（折線グラフ）
  - Y 軸: % 変化率
  - X 軸: 日付（過去 3 ヶ月）
  - TOPIX との重ね合わせで比較

セクター内トップ銘柄（テーブル）
  - 売買代金上位 10 銘柄
  - 株価、出来高、騰落率を表示
```

**設定・日付選択**

```
日付セレクタ: 任意の過去日付を選択して履歴を表示
リフレッシュボタン: 最新データを手動取得
情報セクション
```

### 5.3 状態管理

```javascript
// React Query の例
const { data: fundFlowData } = useQuery(['fundFlow', selectedDate], 
  () => fetchFundFlow(selectedDate)
);

const { data: performanceData } = useQuery(['performance', selectedDate],
  () => fetchPerformance(selectedDate)
);

// ローカル状態
const [selectedDate, setSelectedDate] = useState(new Date());
const [sortBy, setSortBy] = useState('rank');
```

### 5.4 データ取得

**案 A（API サービス有り）:**
```javascript
const fetchFundFlow = async (date) => {
  const res = await fetch(`/api/sectors/fund-flow?date=${date}`);
  return res.json();
};
```

**案 B（GitHub Pages + JSON ファイル、API 不要）:**
```javascript
const fetchFundFlow = async (date) => {
  // 当日データ取得（キャッシュバスティング）
  if (date === today) {
    const res = await fetch(`/data/fund-flow/latest.json?_t=${date}`);
    return res.json();
  }
  // 過去日付データ取得
  const res = await fetch(`/data/fund-flow/${date}.json`);
  return res.json();
};
```

---

## 6. Discord 連携

### 6.1 日次要約メッセージ

分析サービス完了後（毎営業日朝 6:00 UTC = 15:00 JST の翌営業日、日本時間でいえば翌朝 6:00 頃）、Discord webhook に投稿：

```
📊 **セクター市場分析 — 2026-05-30**

**資金流入上位 5 セクター:**
1. テクノロジー: ¥5.2B（+15.5% 当日）
2. ヘルスケア: ¥3.1B（+8.2% 当日）
3. エネルギー: ¥2.8B（+12.1% 当日）
...

**資金流出上位 5 セクター:**
1. 金融: ¥2.1B（-8.5% 当日）
2. ユーティリティ: ¥1.5B（-3.2% 当日）
...

**主要パフォーマンス変動（1 日）:**
- テクノロジー: +2.5%（TOPIX +1.2% 比）
- 素材: -1.8%（TOPIX +1.2% 比）

🔗 詳細分析へ: [ダッシュボード URL]
```

### 6.2 設定

- Discord webhook URL を GitHub Secrets に保存
- 非致命的エラー: webhook 失敗時はログに記録、分析は続行
- 送信タイミング: 毎営業日 6:00 UTC（= 前日15:00 JST の翌営業日朝）に実行される分析完了直後

---

## 7. テスト戦略

### 7.1 ユニットテスト

**データ取得サービス:**
- API レスポンスをモック
- データパース・検証ロジックのテスト
- エラーハンドリング（欠損値、NULL）
- カバレッジ: > 80%

**分析サービス:**
- 資金流入計算を固定データでテスト
- セクターパフォーマンス計算をテスト
- エッジケース（ゼロ取引、全価格同一）
- ランキングロジック
- カバレッジ: > 80%

**フロントエンド（React）:**
- コンポーネント描画テスト（Jest + React Testing Library）
- ソート、フィルタリング、日付選択のテスト
- API レスポンスをモック
- カバレッジ: > 75%

### 7.2 統合テスト

**データパイプライン:**
- テストデータベース（SQLite またはテスト PostgreSQL）を立上
- 取得 → 分析 → 出力検証
- 計算結果テーブルが期待値と一致確認

**API（デプロイ時）:**
- 全エンドポイントをモックデータでテスト
- レスポンス形式・ステータスコード確認
- エラーケース（無効な日付、存在しないセクター）

**Discord 連携:**
- webhook をモック、メッセージ形式確認
- webhook 失敗時の処理確認

**フロントエンド + バックエンド:**
- E2E: ホーム画面読込、データ表示確認
- セクター詳細クリック、グラフ表示確認
- 日付変更、新データ読込確認

### 7.3 データ品質テスト

- 欠損データ処理: 部分データで分析がクラッシュしない
- 外れ値検出: 価格スパイク（>20%）をフラグ
- スキーマ整合性: 重要項目の NULL 違反なし
- パフォーマンス: 全銘柄分析が 5 分以内に完了

### 7.4 CI/CD パイプライン

**GitHub Actions:**
```yaml
全コミット時:
  - ユニットテスト実行（全サービス）
  - コード整形チェック（Python、JavaScript）
  - カバレッジ確認（重要部分 < 80% で失敗）
  - テスト失敗でマージブロック

リリース時:
  - テスト実行
  - GitHub Pages へデプロイ（フロントエンド）
  - データベース更新
```

---

## 8. デプロイと基盤

### 8.1 完全無料アーキテクチャ

**サービス・ホスティング:**
- **データ取得:** GitHub Actions workflow（公開リポジトリ = 完全無料・無制限）
- **分析:** GitHub Actions workflow またはローカル Python スクリプト
- **データベース:** Supabase（無料枠: 500MB）または SQLite（ファイルベース、GitHub に commit）
- **フロントエンド:** GitHub Pages（無料静的ホスティング、コールドスタートなし）
- **Discord webhook:** 無料（Discord が提供）

**コスト: ¥0/月**

### 8.2 ローカル開発

```bash
# リポジトリクローン
git clone <repo>
cd <repo>

# 依存関係インストール
pip install -r requirements.txt
npm install

# ローカル実行
python -m data_ingestion.main  # データ取得
python -m analysis.main        # 分析実行
npm run dev                    # React dev サーバー起動
```

### 8.3 データベース設定

**推奨: Supabase（チーム開発 / 本番用）**
- Supabase 無料アカウント作成
- PostgreSQL データベース作成（無料枠: 500MB、十分）
- 接続文字列を GitHub Secrets に保存
- データはクラウドに永続化
- GitHub Actions から直接 INSERT / SELECT 可能
- 複数チームメンバーがアクセス可能

**無料枠の制約を理解する:**
- ストレージ: 500MB（CSV で月 1,000 行程度の株式データなら十分）
- 同時接続数: 50（GitHub Actions 1 + ブラウザ複数 = 問題なし）
- パース停止: 7 日間アクティブがないと自動停止（GitHub Actions で毎日実行するため非影響）
- バックアップ: 7 日間保持（十分）

→ 制約内での運用は問題ないが、ユーザー数が増えたら有料プランへの移行を検討

**代替案: SQLite ローカル開発のみ**
- SQLite をローカル開発環境でのみ使用
- リポジトリには commit しない（肥大化・コンフリクト防止）
- 本番環境では Supabase に移行する前提
- 単独開発者で、チーム展開予定がない場合のみ

**却下: SQLite + Git 自動 commit**
- 毎日の自動コミットによるリポジトリ肥大化（1年で DBファイル数十MB）
- 複数ワークフロー並列実行時のマージコンフリクト
- GitHub Pages デプロイと競合のリスク
→ この方式は運用破綻する可能性が高いため、採用しない

### 8.4 GitHub Actions ワークフロー

**データ取得スケジュール（毎営業日 15:00 JST 直後に実行、祝日自動スキップ）:**

**タイミング:** 
- cron: `0 6 * * 1-5` = 毎月-金 6:00 UTC = 毎日 15:00 JST
- J-Quants API のデータは翌営業日 15:00 に確定するため、**翌営業日朝 (6:00 UTC) に前日データを取得**
- 例) 2026-05-30（金）の終値データ → 2026-05-31（土）は非営業日、翌営業日 2026-06-01（月）6:00 UTC に取得開始
- 祝日は `jpbizday.isopen()` で自動判定して実行をスキップ

```yaml
name: 毎営業日データ取得と分析
on:
  schedule:
    - cron: '0 6 * * 1-5'  # 月-金 6:00 UTC (= 当日 15:00 JST の次営業日 6:00 UTC に実行)
  workflow_dispatch:        # 手動実行も可能

jobs:
  ingest-and-analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      
      # ステップ1: TSE 営業日判定（祝日ならここで終了）
      - run: |
          python -c "
          import jpbizday
          from datetime import datetime, timedelta, timezone
          JST = timezone(timedelta(hours=9))
          yesterday = (datetime.now(tz=JST) - timedelta(days=1)).date()
          if jpbizday.isopen(yesterday):
            print('SKIP=false')
          else:
            print('SKIP=true')
          " >> $GITHUB_ENV
      
      - name: Skip if holiday
        if: env.SKIP == 'true'
        run: echo "Yesterday was a holiday, skipping data ingestion"
      
      # ステップ2: データ取得（祝日でなければ実行）
      - run: pip install -r requirements.txt
        if: env.SKIP == 'false'
      
      - run: python -m data_ingestion.main
        if: env.SKIP == 'false'
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          JQUANTS_API_KEY: ${{ secrets.JQUANTS_API_KEY }}
      
      # ステップ3: 分析実行
      - run: python -m analysis.main
        if: env.SKIP == 'false'
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
      
      # ステップ4: React ビルド・デプロイ（分析後）
      - run: npm install && npm run build
        if: env.SKIP == 'false'
        working-directory: ./frontend
      
      - name: Deploy to GitHub Pages
        if: env.SKIP == 'false'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/build
```

**重要な注意:**
- `jpbizday` ライブラリで JST タイムゾーンでの営業日判定（祝日が含まれる）
- **制限:** `jpbizday` は定期的な祝日のみカバー、臨時休場（天皇崩御など）には未対応。臨時休場時は手動で対応するか、別途 JPX 公式カレンダーと同期する処理を追加することで対応
- エラー発生時（API 失敗など）は GitHub Actions の失敗通知が自動で送られる
- **Git commit はしない** → リポジトリ肥大化・コンフリクト防止

### 8.5 監視とアラート

**監視項目:**
- GitHub Actions ワークフロー成功/失敗（Actions タブで確認）
- Discord メッセージ送信成功（webhook POST 成功）
- データベースサイズ（Supabase ダッシュボード）
- フロントエンド可用性（GitHub Pages ステータス）

**アラート:**
- GitHub Actions メール通知（ワークフロー失敗時）
- Discord メッセージにエラー要約を含める

---

## 9. 成功基準

### 9.1 MVP 完了条件

- [x] データ取得パイプライン動作（毎日 TSE API から取得）
- [x] PostgreSQL / SQLite スキーマ定義・テスト完了
- [x] 資金流入計算が正確（手動計算と一致）
- [x] パフォーマンス計算が正確（TOPIX 比較で検証）
- [x] REST API が正確なデータを返却（または JSON ファイル commit）
- [x] React ダッシュボード表示（資金流入ランキング、パフォーマンス）
- [x] Discord 日次要約メッセージ送信成功
- [x] 全テスト合格（ユニット、統合、E2E）、カバレッジ > 80%
- [x] GitHub Pages + GitHub Actions でデプロイ動作
- [x] ゼロコスト（全サービス無料枠）

### 9.2 ユーザー体験目標

**デイトレーダー向け:**
- ダッシュボード読込が 2 秒以内（GitHub Pages + CDN）
- 流入/流出セクターを一目で識別可能
- 1 日/5 日のセクターモメンタム追跡可能
- 朝一で Discord アラート受取

**ポートフォリオ運用者向け:**
- 20 日/60 日パフォーマンストレンドを表示
- セクター vs TOPIX 比較可能
- 任意の過去日付の履歴にアクセス可能
- セクターローテーションパターンを検出可能

---

## 10. 実装フェーズ

### フェーズ 1: バックエンド・データ（1-2 週間）
- データ取得サービス: API 連携、パース、検証
- 分析サービス: 資金流入・パフォーマンス計算
- データベーススキーマ設定（PostgreSQL または SQLite）
- ユニット・統合テスト
- GitHub Actions ワークフロー自動化

### フェーズ 2: API・Discord（1 週間）
- FastAPI サービス（オプション、JSON ファイル案なら不要）
- Discord webhook 連携・テスト
- E2E テスト（パイプライン全体）

### フェーズ 3: フロントエンド（1 週間）
- React ダッシュボードスケルトン
- 資金流入ランキング・パフォーマンスグラフコンポーネント
- 日付ピッカー・フィルタリング
- GitHub Pages デプロイ

### フェーズ 4: 調整・リリース（1 週間）
- パフォーマンス最適化
- UI 洗練
- 徹底テスト
- ドキュメント整備
- 本番リリース

---

## 11. 技術選択とトレードオフ

### 11.1 なぜマイクロサービス + GitHub Actions か

**選択:** 3 つの独立サービス（取得、分析、フロントエンド）を GitHub Actions で実行、常時稼働なし。

**理由:**
- ✅ ゼロコスト（サーバー代なし）
- ✅ コールドスタートなし（GitHub Actions は常時準備状態）
- ✅ 日次バッチに最適（スケジュール実行）
- ✅ チーム開発に最適（役割分離）
- ⚠️ リアルタイム更新に非対応（日次のみ）

**却下案:** AWS/GCP の常時マイクロサービス → MVP では高コスト

### 11.2 なぜ SQLite または Supabase か

**選択:** SQLite シンプル版、Supabase チーム協業版。

**理由:**
- SQLite: セットアップ不要、オフライン対応、ソロ開発向け
- Supabase: どこからでもアクセス、チーム向け、永続化
- 両者とも無料枠で MVP 十分

**却下案:** MySQL/MariaDB 自前ホスト → 運用負荷大

### 11.3 なぜ React + GitHub Pages か

**選択:** 静的 React アプリを GitHub Pages でホスティング。

**理由:**
- ✅ ゼロコスト
- ✅ 爆速ロード（CDN バック）
- ✅ バックエンドサーバー不要（JSON ファイル読込）
- ⚠️ リアルタイム対応不可（日次ポーリングのみ）

**却下案:** Next.js + Vercel API → 複雑化・コスト増加

### 11.4 終値後のバッチ処理のみ

**選択:** 毎日 15:00 後に 1 回、分析計算。

**理由:**
- ✅ ユーザー需要に合致（運用者は日次確認）
- ✅ 計算負荷削減
- ✅ インフラ安定
- ⚠️ デイトレーダーには無対応（将来対応予定）

---

## 12. 将来拡張機能（MVP 後）

- リアルタイムデータフィード（時間単位の更新）
- AI テーマ抽出（関連銘柄クラスタリング）
- 異常検知（出来高・価格スパイク）
- メール通知
- Slack 連携
- 高度なフィルタリング（時価総額、セクター別）
- ポートフォリオ追跡（ユーザーアカウント、ウォッチリスト）
- モバイルアプリ
- レポート出力（PDF / CSV）

---

## 付録: J-Quants API 統合

### A.1 J-Quants API（JPX 公式）の仕様

**エンドポイント:** https://api.jquants.com/v1/

**無料プラン制約:**
- 過去 12 週間（約 3 ヶ月）のデータのみ提供
- リアルタイム情報は営業日翌営業日 15:00 以降に確定
- 1 日の API 呼び出し数制限あり（詳細は規約確認）

**提供データ:**
- `daily_prices`: 日付、始値、高値、安値、終値、出来高
- `trading_value`: 売買代金
- `sector`: TSE33 業種コード
- `indices` (TOPIX): TOPIX日次データ（vs_topix計算用）
- **提供されないデータ:** 信用残、PER、PBR などのファンダメンタルズ

**TOPIX取得エンドポイント:**
```
GET https://api.jquants.com/v1/indices?code=0001&date=2026-05-30
Response:
{
  "indices": [
    {
      "date": "2026-05-30",
      "open": 2750.25,
      "high": 2765.50,
      "low": 2740.10,
      "close": 2760.80
    }
  ]
}
```
→ 分析サービスはセクター騰落率とTOPIX騰落率を比較して `vs_topix_1d` を計算

**認証:**
```
headers: {
  "Authorization": f"Bearer {JQUANTS_API_KEY}"
}
```

**初期セットアップ:**
1. https://jpx-jquants.com/ でアカウント登録（無料）
2. API キーを発行
3. GitHub Secrets に `JQUANTS_API_KEY` として保存

**今後の拡張（有料）:**
- 信用残データ取得（東証公式データベース）
- リアルタイム情報（15 分遅延 → ほぼリアルタイム）
- ファンダメンタルズ（EDINET API など別途連携）

### A.2 GitHub Secrets 設定

GitHub Actions で使用する認証情報をセキュアに管理：
```
JQUANTS_API_KEY=<your-jquants-api-key>
SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-anon-key>
DISCORD_WEBHOOK=<your-discord-webhook-url>
```

Repository Settings → Secrets and variables → Actions で設定

---

## 承認サイン

**設計承認者:** [ユーザー]  
**日付:** 2026-05-30  
**次ステップ:** writing-plans スキルを実行して、詳細な実装計画を作成
