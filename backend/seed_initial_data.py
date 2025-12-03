#!/usr/bin/env python3
"""
初期データ投入スクリプト
カテゴリと管理ユーザーを作成
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.category import Category
from app.models.ai_settings import AISettings
from app.utils.security import get_password_hash

def seed_categories(db: Session):
    """カテゴリの初期データを作成"""
    print("\n📂 カテゴリを作成中...")

    categories = [
        {"name": "食費", "color": "#FF6B6B", "icon": "🍽️", "sort_order": 1},
        {"name": "飲料", "color": "#4ECDC4", "icon": "☕", "sort_order": 2},
        {"name": "日用品", "color": "#45B7D1", "icon": "🧴", "sort_order": 3},
        {"name": "交通費", "color": "#FFA07A", "icon": "🚗", "sort_order": 4},
        {"name": "娯楽", "color": "#98D8C8", "icon": "🎮", "sort_order": 5},
        {"name": "衣類", "color": "#F7DC6F", "icon": "👔", "sort_order": 6},
        {"name": "医療", "color": "#BB8FCE", "icon": "💊", "sort_order": 7},
        {"name": "教育", "color": "#85C1E2", "icon": "📚", "sort_order": 8},
        {"name": "通信費", "color": "#F8B739", "icon": "📱", "sort_order": 9},
        {"name": "光熱費", "color": "#52B788", "icon": "💡", "sort_order": 10},
        {"name": "家賃", "color": "#E63946", "icon": "🏠", "sort_order": 11},
        {"name": "保険", "color": "#457B9D", "icon": "🛡️", "sort_order": 12},
        {"name": "その他", "color": "#95A5A6", "icon": "📦", "sort_order": 99},
    ]

    created_count = 0
    for cat_data in categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
            created_count += 1
            print(f"   ✅ {cat_data['icon']} {cat_data['name']}")

    db.commit()
    print(f"\n✅ {created_count}個のカテゴリを作成しました")


def seed_admin_user(db: Session):
    """管理ユーザーを作成"""
    print("\n👤 管理ユーザーを作成中...")

    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"  # ⚠️ 本番環境では変更すること

    existing_admin = db.query(User).filter(User.username == admin_username).first()
    if existing_admin:
        print(f"   ℹ️  管理ユーザー '{admin_username}' は既に存在します")
        return

    admin_user = User(
        username=admin_username,
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name="管理者",
        is_admin=True,
        is_active=True
    )
    db.add(admin_user)
    db.commit()

    print(f"   ✅ 管理ユーザー '{admin_username}' を作成しました")
    print(f"      - Email: {admin_email}")
    print(f"      - Password: {admin_password}")
    print(f"      ⚠️  本番環境では必ずパスワードを変更してください！")


def seed_ai_settings(db: Session):
    """AI設定のデフォルト値を作成"""
    print("\n🤖 AI設定を作成中...")

    existing = db.query(AISettings).first()
    if existing:
        print(f"   ℹ️  AI設定は既に存在します")
        return

    ai_settings = AISettings(
        ocr_model="gpt-5.1-codex-mini",
        ocr_enabled=True,
        classification_model="gpt-5.1-codex-mini",
        classification_enabled=True,
        sandbox_mode="read-only",
        skip_git_repo_check=True
    )
    db.add(ai_settings)
    db.commit()

    print(f"   ✅ AI設定を作成しました")
    print(f"      - OCRモデル: {ai_settings.ocr_model}")
    print(f"      - 分類モデル: {ai_settings.classification_model}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("🌱 初期データ投入スクリプト")
    print("=" * 60)

    db = SessionLocal()
    try:
        seed_categories(db)
        seed_admin_user(db)
        seed_ai_settings(db)

        print("\n" + "=" * 60)
        print("✅ 初期データの投入が完了しました")
        print("=" * 60)
        print("\n📝 ログイン情報:")
        print("   - ユーザー名: admin")
        print("   - パスワード: admin123")
        print("   - URL: http://localhost:5173")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ エラー: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    main()
