#!/usr/bin/env python3
"""
データベースを削除して再作成するスクリプト
ExpenseItem対応の新スキーマを適用
"""
import sys
from sqlalchemy import create_engine, text
from app.config import settings
from app.database import Base
from app.models.user import User
from app.models.category import Category
from app.models.expense import Expense
from app.models.expense_item import ExpenseItem
from app.models.receipt import Receipt
from app.models.ai_settings import AISettings

def recreate_database():
    """データベースを削除して再作成"""
    print("=" * 60)
    print("🗑️  データベース再作成スクリプト")
    print("=" * 60)

    # 管理者用接続（データベースなし）
    admin_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}"
    admin_engine = create_engine(admin_url)

    try:
        with admin_engine.connect() as conn:
            # データベース削除
            print(f"\n❌ データベース '{settings.DB_NAME}' を削除中...")
            conn.execute(text(f"DROP DATABASE IF EXISTS `{settings.DB_NAME}`"))
            conn.commit()
            print(f"✅ データベース '{settings.DB_NAME}' を削除しました")

            # データベース作成
            print(f"\n🆕 データベース '{settings.DB_NAME}' を作成中...")
            conn.execute(text(f"CREATE DATABASE `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"✅ データベース '{settings.DB_NAME}' を作成しました")

    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        sys.exit(1)
    finally:
        admin_engine.dispose()

    # 新しいスキーマでテーブル作成
    print(f"\n📊 テーブルを作成中...")
    app_engine = create_engine(settings.DATABASE_URL)

    try:
        # 全テーブル作成
        Base.metadata.create_all(bind=app_engine)
        print("✅ 全テーブルを作成しました")

        # 作成されたテーブル一覧を表示
        print("\n📋 作成されたテーブル:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")

        print("\n" + "=" * 60)
        print("✅ データベースの再作成が完了しました")
        print("=" * 60)

    except Exception as e:
        print(f"❌ テーブル作成エラー: {str(e)}")
        sys.exit(1)
    finally:
        app_engine.dispose()

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    response = input("\n⚠️  警告: このスクリプトは既存のデータベースを削除します。続行しますか? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ キャンセルしました")
        sys.exit(0)

    recreate_database()
