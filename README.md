# 東証セクター資金流入分析プラットフォーム

> 東京証券取引所のセクター別資金流入データをリアルタイムで分析・可視化するオープンソースプラットフォーム

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![Node.js](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org)
[![Tests](https://img.shields.io/badge/tests-56%2F57%20passed-brightgreen.svg)](pytest.ini)

## 🎯 プロジェクト概要

このプラットフォームは、日本取引所グループ（JPX）の公式 API である **J-Quants** を活用して、東京証券取引所（TSE）のセクター別資金流入を自動分析します。

毎営業日、GitHub Actions により自動的にデータを取得・分析し、その結果を高度に可視化された React ダッシュボードで表示します。

### 主な特徴

- 📊 **自動分析**: 毎営業日 6:00 UTC（日本時間 15:00）に自動実行
- 📱 **モダン UI**: React 18 + Tailwind CSS による美しいダッシュボード
- 📈 **高度な可視化**: Recharts による複数のインタラクティブチャート
- 💾 **データ永続化**: Supabase PostgreSQL への自動保存
- 🤖 **Discord 統合**: 毎日の分析結果を自動通知
- 🧪 **テスト完備**: 56+ 個の自動テストで品質保証
- 🚀 **デプロイ準備**: GitHub Pages（Frontend）・カスタムホスト（Backend）対応
- 📚 **完全ドキュメント**: 詳細なセットアップガイド・ユーザーマニュアル

---

## 🚀 クイックスタート

### 前提条件
- Python 3.11+
- Node.js 18+
- Supabase アカウント
- J-Quants API キー

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 環境設定ファイルを作成
cp .env.example .env

# .env を編集して以下を設定
# - SUPABASE_URL
# - SUPABASE_KEY
# - JQUANTS_API_KEY

# バックエンド依存関係をインストール
pip install -r requirements.txt

# フロントエンド依存関係をインストール
cd frontend && npm install && cd ..
```

### 起動

```bash
# ターミナル 1: FastAPI サーバー
python -m uvicorn api.main:app --reload

# ターミナル 2: フロントエンド開発サーバー
cd frontend && npm run dev

# ブラウザで http://localhost:3000 にアクセス
```

詳細は [USER_MANUAL.md](USER_MANUAL.md) を参照

---

## 📁 プロジェクト構成

```
.
├── api/                          # FastAPI REST API
├── analysis/                     # 分析エンジン
├── data_ingestion/               # データ取得パイプライン
├── frontend/                     # React フロントエンド
├── .github/workflows/            # GitHub Actions
├── docs/                         # ドキュメント
├── requirements.txt              # Python 依存関係
├── USER_MANUAL.md                # ユーザーマニュアル
└── README.md                     # このファイル
```

---

## 🔧 API エンドポイント

| メソッド | エンドポイント | 説明 |
|---------|-------------|------|
| GET | `/` | ルート |
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/sectors/fund-flow` | 資金流入ランキング |
| GET | `/api/sectors/performance` | パフォーマンスメトリクス |
| GET | `/api/sectors/{id}/history` | 履歴データ |
| GET | `/api/metadata/sectors` | セクター情報 |

詳細: `http://localhost:8000/docs`（起動時）

---

## 📊 テスト結果

```
======================= 56 passed, 1 skipped in 3.90s =======================
```

テストを実行:

```bash
pytest                    # すべてのテスト
pytest --cov            # カバレッジ付き
```

---

## 📚 ドキュメント

- **[ユーザーマニュアル](USER_MANUAL.md)** - インストール、セットアップ、使用方法
- **[デプロイメントガイド](docs/DEPLOYMENT.md)** - 本番環境へのデプロイメント
- **[プロジェクト概要](docs/PROJECT_SUMMARY.md)** - 技術仕様、アーキテクチャ

---

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) を参照してください。

---

## 📞 サポート

問題が発生した場合は [GitHub Issues](../../issues) を作成してください。

---

**Made with ❤️ for Japanese Stock Market Analysis**
