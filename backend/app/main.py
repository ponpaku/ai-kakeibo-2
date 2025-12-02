from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.api.endpoints import auth, users, categories, expenses, receipts, dashboard, ai_settings
import os

# モデルをインポート（テーブル作成のため）
from app.models import user, category, expense, receipt, ai_settings as ai_settings_model

# テーブル作成
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI家計簿 API",
    description="AIを利用した家計簿アプリケーション",
    version="1.0.0"
)

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

# 静的ファイル（レシート画像）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


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
