from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.endpoints import auth, users, categories, expenses, receipts, dashboard, ai_settings
from app.api.endpoints import category_rules
import os
import logging
import time

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# モデルをインポート（テーブル作成のため）
from app.models import user, category, expense, expense_item, receipt, ai_settings as ai_settings_model, category_rule
from app.models.user import User
from app.models.category import Category
from app.utils.security import get_password_hash

logger.info("🚀 Starting AI Kakeibo API...")

# テーブル作成
Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables created/verified")

app = FastAPI(
    title="AI家計簿 API",
    description="AIを利用した家計簿アプリケーション",
    version="1.0.0"
)

# リクエストログミドルウェア
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"📥 {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        logger.error(f"❌ Error processing {request.method} {request.url.path}: {str(e)}")
        raise

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(receipts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ai_settings.router, prefix="/api")
app.include_router(category_rules.router, prefix="/api")

# 静的ファイル（レシート画像）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    db = SessionLocal()
    try:
        # ユーザーの存在確認
        user_count = db.query(User).count()
        if user_count == 0:
            print("初期ユーザーが存在しないため、作成します...")
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
            print("初期ユーザーを作成しました（ユーザー名: admin, パスワード: admin123）")

        # カテゴリの存在確認
        category_count = db.query(Category).count()
        if category_count == 0:
            print("初期カテゴリが存在しないため、作成します...")
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
            print(f"{len(categories)}件の初期カテゴリを作成しました")
    except Exception as e:
        print(f"起動時の初期化エラー: {str(e)}")
        db.rollback()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "AI家計簿 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)
