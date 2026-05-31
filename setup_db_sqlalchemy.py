#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase スキーマ初期化スクリプト（SQLAlchemy を使用）
実行: python setup_db_sqlalchemy.py
"""
import os
import sys
import io
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Windows での UTF-8 出力を有効化
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .env ファイルを読み込み
load_dotenv()

def setup_database():
    """Supabase スキーマを初期化"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("[!] Error: SUPABASE_URL or SUPABASE_KEY not set")
        sys.exit(1)

    print(f"[*] Connecting to Supabase: {url}")

    # スキーマ SQL を読み込み
    with open('sql/schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    try:
        # Supabase PostgreSQL 接続文字列を構築
        # URL から project_id を抽出
        # https://tipbelwwrajvmiacevmp.supabase.co -> tipbelwwrajvmiacevmp
        project_id = url.split('.supabase.co')[0].replace('https://', '')

        # Supabase のコネクションプール URL
        # フォーマット: postgresql://postgres.PROJECT_ID:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
        # 簡易版: postgresql://postgres:PASSWORD@db.supabase.co:5432/postgres (認証用の別キーが必要)

        # Supabase の場合、ユーザー名は postgres.PROJECT_ID
        db_url = f"postgresql://postgres.{project_id}:{key}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

        print("[*] Creating SQLAlchemy engine...")
        engine = create_engine(
            db_url,
            echo=False,
            connect_args={
                "sslmode": "require",
            },
            pool_pre_ping=True
        )

        print("[*] Executing SQL script...")

        # SQL を実行
        with engine.begin() as connection:
            # SQL を分割して実行
            statements = schema_sql.split(';')
            for i, statement in enumerate(statements, 1):
                statement = statement.strip()
                if not statement or statement.startswith('--'):
                    continue

                try:
                    connection.execute(text(statement))
                    print(f"  [+] Step {i} completed")
                except Exception as e:
                    error_msg = str(e)
                    # 既に存在するテーブルやリレーションは無視
                    if "already exists" in error_msg or "duplicate" in error_msg:
                        print(f"  [!] Step {i} skipped (already exists)")
                    else:
                        print(f"  [!] Step {i} error: {error_msg[:100]}")

        print("\n[+] Schema initialization completed!")
        print("[*] Created tables:")
        print("  - sectors (TSE 33 sector master)")
        print("  - master_stocks (stock master)")
        print("  - daily_prices (daily stock prices)")
        print("  - daily_trading (daily trading values)")
        print("  - sector_daily_aggregates (sector aggregation)")
        print("  - sector_performance (sector performance)")
        print("  - sector_fund_flow (fund flow)")

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    setup_database()
