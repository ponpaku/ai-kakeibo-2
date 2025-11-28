"""
データベース初期化スクリプト

初期ユーザーとカテゴリを作成します。
"""

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.category import Category
from app.utils.security import get_password_hash

def init_database():
    """データベースの初期化"""
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
    init_database()
