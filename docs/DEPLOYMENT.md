# デプロイメント ガイド

## フロントエンド デプロイメント (GitHub Pages)

### 前提条件
- GitHub アカウント
- このリポジトリを GitHub にプッシュしていること

### セットアップ手順

#### 1. GitHub リポジトリ設定

1. GitHub でリポジトリを開きます
2. **Settings** → **Pages** に移動
3. **Source** を **GitHub Actions** に設定
4. **Save** をクリック

#### 2. デプロイメント実行

フロントエンドは以下の条件で自動的に GitHub Pages にデプロイされます:

- `main` または `master` ブランチへのプッシュ
- `frontend/` ディレクトリ内のファイル変更
- `.github/workflows/deploy-frontend.yml` ファイルの変更

#### 3. カスタムドメイン (オプション)

GitHub Pages でカスタムドメインを使用する場合:

1. **Settings** → **Pages** → **Custom domain** に移動
2. ドメイン名を入力して **Save** をクリック
3. DNS レコードを設定

### デプロイメント URL

デプロイメント後、以下の URL でアクセスできます:

**デフォルト:**
```
https://<username>.github.io/<repository-name>
```

**カスタムドメイン:**
```
https://your-custom-domain.com
```

### API エンドポイント設定

GitHub Pages にデプロイされたフロントエンドが API にアクセスする場合、API サーバーが外部からアクセス可能である必要があります。

**CORS 設定例 (FastAPI):**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://<username>.github.io", "https://your-custom-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### デプロイメント監視

1. GitHub リポジトリの **Actions** タブを開く
2. **Deploy Frontend to GitHub Pages** ワークフローを確認
3. 各デプロイメントの詳細を確認

### トラブルシューティング

**問題: ページが見つからない (404)**
- リポジトリが公開されていることを確認
- Pages が GitHub Actions をソースとして設定されていることを確認
- ワークフローが成功していることを確認

**問題: API リクエストが失敗**
- API サーバーが起動しており、外部からアクセス可能か確認
- CORS 設定を確認
- ブラウザのコンソール（F12）でエラーメッセージを確認

## バックエンド デプロイメント

バックエンド (FastAPI) のデプロイメントについては、ホスティングプロバイダーに応じて異なります。

### 推奨ホスティング

- **Heroku**: 無料または有料プラン
- **Railway**: 無料トライアル + 従量課金
- **Render**: 無料または有料プラン
- **PythonAnywhere**: Python 専用ホスティング
- **AWS/Google Cloud/Azure**: エンタープライズソリューション

### FastAPI デプロイメント例 (Heroku)

1. Procfile を作成:
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

2. requirements.txt にデプロイメント用の依存関係を追加:
```
gunicorn>=20.1.0
```

3. Heroku CLI でデプロイ:
```bash
heroku login
heroku create <app-name>
git push heroku main
```

## 本番環境設定

### 環境変数

`.env` ファイルをホスティングサービスのシークレット管理に登録:

**必須:**
- `SUPABASE_URL`: Supabase データベース URL
- `SUPABASE_KEY`: Supabase API キー
- `JQUANTS_API_KEY`: J-Quants API キー
- `DISCORD_WEBHOOK`: Discord Webhook URL (オプション)

### セキュリティ

1. 本番環境では `DEBUG = False` に設定
2. API キーと認証情報をシークレット管理に保存
3. HTTPS を使用
4. CORS を限定的に設定
5. レート制限を実装
6. ログとモニタリングを設定

## CI/CD パイプライン

既存のワークフロー:

- **data-ingestion.yml**: 毎営業日 6:00 UTC でデータ取得・分析を実行
- **tests.yml**: 各プッシュで自動テスト実行
- **deploy-frontend.yml**: フロントエンドを GitHub Pages にデプロイ
