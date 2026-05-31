# 東証セクター資金流入分析プラットフォーム - ユーザーマニュアル

**バージョン:** 1.0  
**最終更新:** 2026-05-31  
**言語:** 日本語 / English

---

## 目次

1. [システム要件](#システム要件)
2. [インストール](#インストール)
3. [セットアップ](#セットアップ)
4. [使用方法](#使用方法)
5. [機能ガイド](#機能ガイド)
6. [トラブルシューティング](#トラブルシューティング)
7. [FAQ](#faq)

---

## システム要件

### バックエンド
- **Python:** 3.11 以上
- **データベース:** PostgreSQL（Supabase アカウント推奨）
- **OS:** Windows、macOS、Linux

### フロントエンド
- **Node.js:** 18 以上
- **npm または yarn:** 最新版
- **ブラウザ:** Chrome、Firefox、Safari、Edge（最新版）

### API アクセス
- **J-Quants API キー** （日本取引所グループから取得）
- **Discord Webhook** （オプション、通知機能使用時）

---

## インストール

### ステップ 1: リポジトリのクローン

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### ステップ 2: 環境設定ファイルの作成

`.env.example` をコピーして `.env` を作成:

```bash
cp .env.example .env
```

### ステップ 3: 環境変数の設定

`.env` ファイルを編集して、以下の情報を入力します:

```env
# Supabase 設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# J-Quants API キー
JQUANTS_API_KEY=your-jquants-api-key

# Discord Webhook（オプション）
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...

# 開発設定
DATABASE_TYPE=supabase  # または sqlite
DEBUG=false
```

### ステップ 4: バックエンド依存関係のインストール

```bash
pip install -r requirements.txt
```

### ステップ 5: フロントエンド依存関係のインストール

```bash
cd frontend
npm install
cd ..
```

### ステップ 6: データベーススキーマの初期化

```bash
# Supabase データベースに接続して、sql/schema.sql を実行
# または Supabase コンソールから直接実行
```

---

## セットアップ

### Supabase の設定

1. **Supabase アカウント作成**
   - https://supabase.com にアクセス
   - 無料アカウントを作成

2. **プロジェクト作成**
   - 新しいプロジェクトを作成
   - PostgreSQL データベースを初期化

3. **接続情報取得**
   - Project Settings → API
   - `Project URL` と `anon key` をコピー
   - `.env` に貼り付け

4. **スキーマ初期化**
   - SQL エディタを開く
   - `sql/schema.sql` の内容をコピー&ペースト
   - 実行

### J-Quants API の設定

1. **API キーを取得**
   - https://jpx-jquants.com にアクセス
   - API キーを申請

2. **`.env` に設定**
   ```env
   JQUANTS_API_KEY=your-key-here
   ```

### Discord Webhook の設定（オプション）

1. **Discord サーバーで Webhook を作成**
   - サーバー設定 → 連携サービス → Webhook
   - 新しい Webhook を作成
   - URL をコピー

2. **`.env` に設定**
   ```env
   DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
   ```

---

## 使用方法

### バックエンド操作

#### 1. FastAPI サーバーの起動

```bash
python -m uvicorn api.main:app --reload
```

サーバーは `http://localhost:8000` で起動します

API ドキュメント: `http://localhost:8000/docs`

#### 2. データ取得（手動実行）

```bash
python -m data_ingestion.main
```

処理内容:
- 営業日判定
- 前営業日のデータを J-Quants API から取得
- Supabase に保存

#### 3. 分析実行（手動実行）

```bash
python -m analysis.main
```

処理内容:
- セクター別パフォーマンス計算
- 資金流入スコア算出
- Discord に通知（設定時）

### フロントエンド操作

#### 1. 開発サーバーの起動

```bash
cd frontend
npm run dev
```

フロントエンドは `http://localhost:3000` で起動します

#### 2. 本番ビルド

```bash
cd frontend
npm run build
```

`frontend/dist/` に静的ファイルが生成されます

#### 3. ローカルプレビュー

```bash
cd frontend
npm run preview
```

#### 4. テスト実行

```bash
cd frontend
npm test
```

### 全体ワークフロー

```
┌─────────────────────────────────────────┐
│  1. FastAPI サーバー起動                 │
│     (localhost:8000)                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. フロントエンド開発サーバー起動       │
│     (localhost:3000)                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. ブラウザで http://localhost:3000     │
│     にアクセス                          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  4. ダッシュボードでデータを表示         │
│     - 資金流入ランキング                 │
│     - パフォーマンスメトリクス           │
│     - 出来高分析                        │
└─────────────────────────────────────────┘
```

---

## 機能ガイド

### ダッシュボード

#### 資金流入ランキング
- **流入上位 5 セクター**: 資金が流入しているセクターをリアルタイム表示
- **流出上位 5 セクター**: 資金が流出しているセクターをリアルタイム表示
- **クリック**: セクターをクリックして詳細情報を表示

#### セクター別パフォーマンス
- **1 日リターン**: 本日の騰落率
- **5 日リターン**: 過去 5 営業日の累積リターン
- **TOPIX 比較**: TOPIX との相対パフォーマンス

#### 資金流入推移チャート
- **BarChart**: 上位 10 セクターの売買代金を表示

#### セクターパフォーマンスランキング
- **カラーコード化テーブル**: 各セクターのパフォーマンスを色分け表示
- **複数期間対応**: 1 日、5 日、20 日、60 日のリターン表示

#### セクター別出来高分析
- **AreaChart**: 出来高トレンドを表示
- **統計情報**: 平均、最大、合計売買代金を表示

#### セクター間パフォーマンス比較
- **複数セクター選択**: 最大 5 セクターまで選択可能
- **比較チャート**: 複数セクターのパフォーマンスを並べて比較
- **統計テーブル**: 詳細なパフォーマンスデータを表示

#### データエクスポート
- **CSV ダウンロード**: 現在の分析データを CSV 形式で出力
- **ファイル名**: `sector-analysis-YYYY-MM-DD.csv`

### セクター詳細表示

セクターをクリックすると詳細ページを表示:
- **セクター名と戻るボタン**: ダッシュボードに戻る
- **履歴テーブル**: 過去のパフォーマンスデータを表示
- **日付フィルタ**: 日付を変更して異なる分析結果を表示

### 日付選択

ヘッダーの日付ピッカーで分析日付を変更:
- すべてのチャートとテーブルが自動更新
- 過去のデータを遡って分析可能

---

## トラブルシューティング

### バックエンド関連

#### 問題: `ModuleNotFoundError: No module named 'xxx'`

**原因:** 依存パッケージがインストールされていない

**解決策:**
```bash
pip install -r requirements.txt
```

#### 問題: `SUPABASE_URL not found`

**原因:** `.env` ファイルが見つからないまたは設定されていない

**解決策:**
```bash
cp .env.example .env
# .env ファイルを編集して必要な値を入力
```

#### 問題: データベース接続エラー

**原因:** Supabase の接続情報が間違っている

**確認項目:**
- SUPABASE_URL は `https://` で始まっているか
- SUPABASE_KEY は有効か
- ネットワーク接続は有効か

#### 問題: J-Quants API エラー

**原因:** API キーが無効またはレート制限に達した

**解決策:**
- API キーを確認
- 待機してから再試行
- API ドキュメントを確認

### フロントエンド関連

#### 問題: `npm: command not found`

**原因:** Node.js がインストールされていない

**解決策:**
```bash
# https://nodejs.org からダウンロード・インストール
node --version  # 確認
npm --version   # 確認
```

#### 問題: ポート 3000 が既に使用中

**原因:** 別のプロセスがポート 3000 を使用している

**解決策:**
```bash
# ポート 8080 で起動
npm run dev -- --port 8080
```

#### 問題: API リクエストが失敗する（CORS エラー）

**原因:** バックエンド（localhost:8000）が起動していない

**確認項目:**
- FastAPI サーバーが起動しているか
- ポート 8000 が正しいか
- CORS 設定が有効か

```bash
# 新しいターミナルでバックエンドを起動
python -m uvicorn api.main:app --reload
```

### 共通問題

#### 問題: ビルドが失敗する

**解決策:**
```bash
# node_modules をクリア
cd frontend
rm -rf node_modules package-lock.json
npm install

# キャッシュをクリア
npm cache clean --force

# 再ビルド
npm run build
```

#### 問題: テストが失敗する

**解決策:**
```bash
# すべてのテストを実行
pytest -v

# 特定のテストを実行
pytest data_ingestion/tests/test_main.py -v

# カバレッジを表示
pytest --cov
```

---

## FAQ

### Q1: 毎日自動的にデータは更新されますか？

**A:** はい、GitHub Actions により毎営業日 6:00 UTC（日本時間 15:00）に自動実行されます。GitHub にプッシュしてワークフローを有効にしてください。

---

### Q2: ローカル環境でテストできますか？

**A:** はい、以下のコマンドで手動実行できます:

```bash
# データ取得
python -m data_ingestion.main

# 分析実行
python -m analysis.main
```

---

### Q3: API はどのエンドポイントを提供していますか？

**A:** 以下の 6 つのエンドポイント:

```
GET /                           # ルート
GET /api/health                # ヘルスチェック
GET /api/sectors/fund-flow     # 資金流入ランキング
GET /api/sectors/performance   # パフォーマンス
GET /api/sectors/{id}/history  # 履歴データ
GET /api/metadata/sectors      # セクター情報
```

詳細は `http://localhost:8000/docs` を参照

---

### Q4: Discord 通知は必須ですか？

**A:** いいえ、オプションです。DISCORD_WEBHOOK を設定しない場合、通知機能は無効です。

---

### Q5: 本番環境にデプロイするには？

**A:** `docs/DEPLOYMENT.md` を参照してください:

- **フロントエンド**: GitHub Pages（自動）
- **バックエンド**: Heroku、Railway、Render など

---

### Q6: データベースを SQLite から Supabase に変更できますか？

**A:** はい、`.env` で設定できます:

```env
DATABASE_TYPE=supabase
SUPABASE_URL=your-url
SUPABASE_KEY=your-key
```

---

### Q7: テストカバレッジはどのくらいですか？

**A:** 56/57 テスト合格（98.2%）、カバレッジ 46%+

```bash
pytest --cov
```

---

### Q8: 新しいセクターを追加できますか？

**A:** はい、データベースに直接追加するか、J-Quants API の更新を待ってください。

---

### Q9: カスタムレポートを作成できますか？

**A:** はい、以下の方法があります:

- **CSV エクスポート**: ダッシュボードのボタンで出力
- **API 呼び出し**: 独自のスクリプトで実装
- **カスタムコンポーネント**: React コンポーネントを追加

---

### Q10: サポートを受けるには？

**A:** 以下の方法でサポートを受けられます:

- **GitHub Issues**: バグ報告・機能リクエスト
- **ドキュメント**: `docs/` フォルダを参照
- **コードコメント**: 各ファイルにコメント記載

---

## セキュリティに関する注意

### ⚠️ 重要

本番環境で使用する場合:

1. **`.env` ファイルを共有しない**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **API キーをシークレット管理に保存**
   - GitHub Secrets
   - 環境変数管理ツール

3. **HTTPS を使用**
   - 本番環境では必ず HTTPS

4. **CORS を制限**
   ```python
   allow_origins=["https://your-domain.com"]
   ```

5. **レート制限を実装**
   - API リクエスト数を制限

---

## ベストプラクティス

### バックエンド

1. **定期的にテストを実行**
   ```bash
   pytest --cov
   ```

2. **ログを監視**
   - GitHub Actions のワークフロー実行ログ
   - Supabase のログ

3. **データベースをバックアップ**
   - Supabase 自動バックアップ機能を有効化

### フロントエンド

1. **本番環境でビルド**
   ```bash
   npm run build
   ```

2. **ブラウザキャッシュを確認**
   - F12 → キャッシュをクリア

3. **パフォーマンスを監視**
   - lighthouse で計測

---

## 追加リソース

- **プロジェクト概要**: `docs/PROJECT_SUMMARY.md`
- **デプロイメント**: `docs/DEPLOYMENT.md`
- **API ドキュメント**: `http://localhost:8000/docs`
- **J-Quants API**: https://jpx-jquants.com
- **Supabase**: https://supabase.com

---

## バージョン履歴

| バージョン | 日付 | 説明 |
|-----------|------|------|
| 1.0 | 2026-05-31 | 初版リリース |

---

## ライセンスと著作権

このプロジェクトは教育・研究目的で作成されました。

利用規約を確認し、必要な場合はライセンスを設定してください。

---

**サポートが必要な場合は GitHub Issues を作成してください**
