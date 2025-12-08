"""
データベース初期化スクリプト

初期ユーザーとカテゴリを作成します。
"""

import os
import sys

def check_environment():
    """環境設定のチェック"""
    # .envファイルの存在確認
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_example_file = os.path.join(os.path.dirname(__file__), '..', '.env.example')

    if not os.path.exists(env_file):
        print("=" * 60)
        print("エラー: .env ファイルが見つかりません")
        print("=" * 60)
        print("\n.env ファイルを作成する必要があります。")
        print("\n以下の手順を実行してください：")
        print("\n1. プロジェクトルートディレクトリに移動:")
        print("   cd ..")
        print("\n2. .env.example から .env をコピー:")
        if os.path.exists(env_example_file):
            print("   cp .env.example .env  # Linux/Mac")
            print("   copy .env.example .env  # Windows")
        else:
            print("   .env.example ファイルも見つかりません。")
            print("   README.md を参照して .env ファイルを手動で作成してください。")

        print("\n3. .env ファイルを編集して以下を設定:")
        print("   - DB_USER (MariaDBのユーザー名)")
        print("   - DB_PASSWORD (MariaDBのパスワード)")
        print("   - SECRET_KEY (ランダムな文字列)")
        print("\n4. 再度このスクリプトを実行:")
        print("   python init_db.py")
        print("=" * 60)
        sys.exit(1)

    # 環境変数の読み込みを試行
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)

        # 必須フィールドのチェック
        required_fields = {
            'DB_USER': os.getenv('DB_USER'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'SECRET_KEY': os.getenv('SECRET_KEY')
        }

        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            print("=" * 60)
            print("エラー: 必須フィールドが設定されていません")
            print("=" * 60)
            print("\n以下のフィールドを .env ファイルに設定してください：")
            for field in missing_fields:
                print(f"  - {field}")
            print("\n.env ファイルの場所:", os.path.abspath(env_file))
            print("\n設定例:")
            print("  DB_USER=your_db_user")
            print("  DB_PASSWORD=your_db_password")
            print("  SECRET_KEY=your-random-secret-key-here")
            print("\n詳細は README.md または SETUP.md を参照してください。")
            print("=" * 60)
            sys.exit(1)

    except Exception as e:
        print("=" * 60)
        print("エラー: 環境変数の読み込みに失敗しました")
        print("=" * 60)
        print(f"\n詳細: {str(e)}")
        print("\n.env ファイルの形式が正しいか確認してください。")
        print("=" * 60)
        sys.exit(1)

def init_database():
    """データベースの初期化"""
    from app.database import SessionLocal, engine, Base
    # 全モデルをインポート（テーブル作成のため必須）
    from app.models.user import User
    from app.models.category import Category
    from app.models.expense import Expense
    from app.models.expense_item import ExpenseItem
    from app.models.receipt import Receipt
    from app.models import ai_settings, category_rule
    from app.utils.security import get_password_hash

    print("データベースの初期化を開始します...")

    # テーブルの作成
    print("テーブルを作成しています...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 既存のユーザーをチェック
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("管理者ユーザーは既に存在します")
        else:
            # 管理者ユーザーを作成
            print("管理者ユーザーを作成しています...")
            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="管理者",
                hashed_password=get_password_hash("admin123"),
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("管理者ユーザーを作成しました（ユーザー名: admin, パスワード: admin123）")

        # 既存のカテゴリをチェック
        existing_categories = db.query(Category).count()
        if existing_categories > 0:
            print(f"カテゴリは既に{existing_categories}件存在します")
        else:
            # カテゴリを作成
            print("カテゴリを作成しています...")
            categories = [
                Category(
                    name="食費",
                    description="食材、外食など",
                    color="#EF4444",
                    icon="shopping-cart",
                    sort_order=1
                ),
                Category(
                    name="日用品",
                    description="生活必需品",
                    color="#F59E0B",
                    icon="home",
                    sort_order=2
                ),
                Category(
                    name="交通費",
                    description="電車、バス、ガソリン代",
                    color="#10B981",
                    icon="car",
                    sort_order=3
                ),
                Category(
                    name="娯楽",
                    description="趣味、レジャー",
                    color="#3B82F6",
                    icon="music",
                    sort_order=4
                ),
                Category(
                    name="医療費",
                    description="病院、薬代",
                    color="#8B5CF6",
                    icon="heart",
                    sort_order=5
                ),
                Category(
                    name="光熱費",
                    description="電気、ガス、水道",
                    color="#EC4899",
                    icon="zap",
                    sort_order=6
                ),
                Category(
                    name="通信費",
                    description="スマホ、インターネット",
                    color="#06B6D4",
                    icon="smartphone",
                    sort_order=7
                ),
                Category(
                    name="その他",
                    description="その他の支出",
                    color="#6B7280",
                    icon="more-horizontal",
                    sort_order=99
                ),
            ]

            for cat in categories:
                db.add(cat)
            db.commit()
            print(f"{len(categories)}件のカテゴリを作成しました")

        print("データベースの初期化が完了しました！")
        print("\n次のステップ:")
        print("1. run.sh (Linux/Mac) または run.bat (Windows) を実行してアプリケーションを起動")
        print("2. http://localhost:5173 にアクセス")
        print("3. ユーザー名: admin, パスワード: admin123 でログイン")
        print("\n重要: 初回ログイン後、必ずパスワードを変更してください！")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # 環境設定のチェック
    check_environment()

    # データベースの初期化
    init_database()
