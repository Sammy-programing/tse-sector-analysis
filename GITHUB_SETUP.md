# GitHub へのプッシュガイド

このプロジェクトを GitHub にプッシュするための手順です。

---

## ステップ 1: GitHub でリポジトリを作成

1. **GitHub にログイン**: https://github.com/login

2. **新しいリポジトリを作成**: https://github.com/new
   - Repository name: `sector-analysis-platform`
   - Description: `東証セクター資金流入分析プラットフォーム`
   - Public を選択（他のユーザーが見られるように）
   - ✅ "Add a README file" は **チェック不要**（既に README.md がある）
   - ✅ "Add .gitignore" を選択 → Python を選択
   - License: MIT を選択
   - **Create repository** をクリック

3. **リポジトリページからクローン URL をコピー**
   ```
   https://github.com/your-username/sector-analysis-platform.git
   ```

---

## ステップ 2: ローカルリポジトリに GitHub リモートを設定

```bash
cd "D:\アプリ開発プロジェクト\投資管理アプリ 試作２号"

# リモートリポジトリを追加
git remote add origin https://github.com/your-username/sector-analysis-platform.git

# リモートを確認
git remote -v
```

出力:
```
origin  https://github.com/your-username/sector-analysis-platform.git (fetch)
origin  https://github.com/your-username/sector-analysis-platform.git (push)
```

---

## ステップ 3: ブランチを リセット（初回のみ）

```bash
# main ブランチに変更（必要に応じて）
git branch -M main
```

---

## ステップ 4: GitHub にプッシュ

### オプション A: HTTPS を使用（推奨）

```bash
# 初回プッシュ
git push -u origin main

# パスワード入力時は Personal Access Token を使用
# GitHub Settings → Developer settings → Personal access tokens
# → Generate new token (classic)
# → Scopes: repo, workflow を選択
# → トークンをコピーしてパスワードとして使用
```

### オプション B: SSH を使用（高度）

```bash
# SSH キーがない場合は生成
ssh-keygen -t ed25519 -C "your-email@example.com"

# GitHub に公開鍵を登録
# https://github.com/settings/keys

# SSH でプッシュ
git remote set-url origin git@github.com:your-username/sector-analysis-platform.git
git push -u origin main
```

---

## ステップ 5: GitHub Pages の設定

フロントエンドを自動的にデプロイするために設定します。

### 5.1: リポジトリ設定

1. GitHub リポジトリを開く
2. **Settings** → **Pages**
3. **Source** を **GitHub Actions** に設定
4. **Save** をクリック

### 5.2: デプロイメント確認

1. **Actions** タブを開く
2. **Deploy Frontend to GitHub Pages** を確認
3. リポジトリにプッシュすると自動的にデプロイされます

---

## ステップ 6: GitHub Secrets の設定（バックエンド自動実行用）

GitHub Actions が毎営業日データを取得・分析するために、秘密情報を登録します。

1. リポジトリを開く
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** をクリック

以下のシークレットを追加:

```
Name: SUPABASE_URL
Value: https://your-project.supabase.co
```

```
Name: SUPABASE_KEY
Value: your-anon-key
```

```
Name: JQUANTS_API_KEY
Value: your-jquants-api-key
```

```
Name: DISCORD_WEBHOOK
Value: https://discord.com/api/webhooks/...
（オプション）
```

---

## ステップ 7: 最初のプッシュ後の確認

### プッシュ確認

```bash
# GitHub に同期されたか確認
git log -1

# 現在のブランチを確認
git branch -v
```

### GitHub でのチェック

1. **Code** タブ: すべてのファイルが表示される
2. **Actions** タブ: CI/CD ワークフローが実行される
3. **Pages** タブ: デプロイメント URL が表示される

---

## 以降のワークフロー

### ローカルで変更を加える

```bash
# 変更を追加
git add .

# コミット
git commit -m "feat: Add new feature"

# GitHub にプッシュ
git push
```

### 自動テストとデプロイ

```
push → GitHub Actions 自動実行
       ├── Tests (pytest)
       ├── Data Ingestion (毎営業日 6:00 UTC)
       └── Frontend Deploy (GitHub Pages)
```

---

## トラブルシューティング

### 問題: "permission denied"

**解決策:**
```bash
# SSH キーの確認
ssh -T git@github.com

# HTTPS の場合は Personal Access Token を使用
git remote set-url origin https://github.com/your-username/repo.git
```

### 問題: "fatal: refusing to merge unrelated histories"

**解決策:**
```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### 問題: Large files warning

**.gitignore を確認:**
```bash
# node_modules や .env が .gitignore に入っているか確認
cat .gitignore | grep -E "node_modules|\.env|__pycache__"
```

---

## GitHub Pages デプロイメント URL

デプロイ後、以下のURL でアクセスできます:

```
https://your-username.github.io/sector-analysis-platform
```

---

## GitHub Actions ワークフロー

### 1. Tests (CI/CD)

- **トリガー**: push, pull request
- **実行内容**: pytest, カバレッジ測定

### 2. Data Ingestion

- **トリガー**: 毎営業日 6:00 UTC
- **実行内容**: データ取得、分析、Discord 通知

### 3. Frontend Deploy

- **トリガー**: main にプッシュ（frontend/ 変更時）
- **実行内容**: npm run build, GitHub Pages へデプロイ

---

## セキュリティチェックリスト

- ✅ `.env` ファイルが `.gitignore` に入っているか
- ✅ API キーが GitHub Secrets に登録されているか
- ✅ リポジトリが Public か Private か確認
- ✅ branch protection rules を設定（オプション）

---

## GitHub コラボレーション

### チーム開発を始める

1. **Collaborators を追加**
   - Settings → Collaborators

2. **Branch protection rules を設定**
   - Settings → Branches → Add rule
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass

3. **Issue / Project を使用**
   - Issues: バグ報告・機能リクエスト
   - Projects: Kanban ボードで進捗管理

---

## 参考リンク

- **GitHub Docs**: https://docs.github.com
- **Personal Access Tokens**: https://github.com/settings/tokens
- **GitHub Pages**: https://pages.github.com
- **GitHub Actions**: https://github.com/features/actions

---

**プッシュ完了後は、GitHub Actions が自動的にテスト・デプロイを開始します！**
