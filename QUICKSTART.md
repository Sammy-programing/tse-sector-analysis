# クイックスタートガイド

東証セクター資金流入分析プラットフォームを 5 分で起動します。

---

## 前提条件

以下がインストール済みであることを確認:

```bash
python --version      # 3.11以上
node --version        # 18以上
npm --version
```

---

## ステップ 1: 環境設定（2分）

```bash
# リポジトリをクローン
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 環境ファイルを作成
cp .env.example .env
```

`.env` を編集して、以下を入力:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
JQUANTS_API_KEY=your-jquants-api-key
DISCORD_WEBHOOK=     # オプション
```

---

## ステップ 2: バックエンド起動（1分）

```bash
pip install -r requirements.txt

# 新しいターミナルウィンドウで実行
python -m uvicorn api.main:app --reload
```

✅ `http://localhost:8000/docs` でAPI ドキュメントが表示されたら成功

---

## ステップ 3: フロントエンド起動（2分）

```bash
cd frontend
npm install
npm run dev
```

✅ `http://localhost:3000` で Vite の起動メッセージが表示されたら成功

---

## ステップ 4: ブラウザで起動

```
http://localhost:3000
```

これで完了！ダッシュボードが表示されます。

---

## よくある問題

### ポート 3000 または 8000 が既に使用中

```bash
# フロントエンドをポート 8080 で起動
npm run dev -- --port 8080
```

### CORS エラーが表示される

バックエンドが起動していることを確認:

```bash
curl http://localhost:8000/api/health
# {"status":"OK"} が返ればOK
```

### モジュールがインストールできない

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## 次のステップ

1. [USER_MANUAL.md](USER_MANUAL.md) で詳細な使用方法を確認
2. `http://localhost:8000/docs` で API ドキュメントを確認
3. データベースをセットアップ（Supabase スキーマ初期化）

---

## テスト実行

```bash
# 全テスト
pytest

# テストカバレッジ付き
pytest --cov

# 特定のモジュールのみ
pytest api/tests/ -v
```

---

## 本番環境へのデプロイ

詳細は [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) を参照

```bash
# フロントエンドビルド
cd frontend && npm run build

# GitHub にプッシュで自動デプロイ（GitHub Actions）
git add .
git commit -m "Deploy to production"
git push origin main
```

---

**問題が発生した場合は [GitHub Issues](../../issues) を作成してください**
