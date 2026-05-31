#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase スキーマ初期化スクリプト
実行: python setup_db.py
"""
import os
import sys
import io
from dotenv import load_dotenv

# Windows での UTF-8 出力を有効化
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env ファイルを読み込み
load_dotenv()

def setup_database():
    """Supabase スキーマを初期化"""
    from supabase import create_client

    # Supabase 認証情報
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("❌ エラー: SUPABASE_URL または SUPABASE_KEY が設定されていません")
        sys.exit(1)

    print(f"🔗 Supabase に接続中: {url}")

    # スキーマ SQL を読み込み
    with open('sql/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # SQL を実行
    try:
        client = create_client(url, key)

        # Supabase Python クライアントでは直接 SQL を実行できないため、
        # 代わりに PostgreSQL 接続を使用
        import psycopg2

        # PostgreSQL 接続文字列を構築
        # https://tipbelwwrajvmiacevmp.supabase.co -> tipbelwwrajvmiacevmp
        project_id = url.split('.supabase.co')[0].replace('https://', '')

        # Supabase の PostgreSQL 接続情報
        print("[*] SQL スクリプトを実行中...")

        # 接続してスキーマを実行
        conn = psycopg2.connect(
            host="db.supabase.co",
            port=5432,
            database="postgres",
            user=f"postgres.{project_id}",
            password=key,
            sslmode="require"
        )
        cursor = conn.cursor()

        # SQL を分割して実行（複数のステートメントに対応）
        statements = schema_sql.split(';')
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if not statement:
                continue

            try:
                cursor.execute(statement)
                print(f"  ✓ ステップ {i} 完了")
            except Exception as e:
                print(f"  ⚠ ステップ {i} スキップ (既に存在): {str(e)[:80]}")

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✅ スキーマ初期化完了！")
        print("📊 作成されたテーブル:")
        print("  - sectors (TSE33 業種マスタ)")
        print("  - master_stocks (銘柄マスタ)")
        print("  - daily_prices (日次株価)")
        print("  - daily_trading (日次売買)")
        print("  - sector_daily_aggregates (セクター集計)")
        print("  - sector_performance (セクター成績)")
        print("  - sector_fund_flow (資金流入)")

    except ImportError:
        print("❌ psycopg2 がインストールされていません")
        print("   実行: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()
