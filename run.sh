#!/bin/bash

# AI家計簿アプリケーション起動スクリプト

set -e

echo "========================================"
echo "AI家計簿 起動スクリプト"
echo "========================================"

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 環境変数ファイルのチェック
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .envファイルが見つかりません${NC}"
    echo "サンプルファイルからコピーしています..."
    cp .env.example .env
    echo -e "${RED}重要: .envファイルを編集してDB接続情報などを設定してください${NC}"
    echo "設定後、このスクリプトを再実行してください"
    exit 1
fi

# Python venv環境のチェックと作成
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Python仮想環境を作成しています...${NC}"
    cd backend
    python3 -m venv venv
    cd ..
fi

# バックエンドの依存関係インストール
echo -e "${GREEN}バックエンドの依存関係をインストールしています...${NC}"
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

# フロントエンドの依存関係インストール
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${GREEN}フロントエンドの依存関係をインストールしています...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Redisの起動チェック
echo -e "${YELLOW}Redisサーバーの起動を確認してください${NC}"
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}警告: redis-cliが見つかりません。Redisがインストールされていることを確認してください${NC}"
else
    if ! redis-cli ping &> /dev/null; then
        echo -e "${YELLOW}Redisサーバーが起動していません。起動しています...${NC}"
        redis-server --daemonize yes
    else
        echo -e "${GREEN}Redisサーバーは既に起動しています${NC}"
    fi
fi

# アップロードディレクトリの作成
mkdir -p uploads/receipts

# データベースマイグレーションの実行
echo -e "${GREEN}データベースマイグレーションを実行しています...${NC}"
cd backend
source venv/bin/activate
# Alembicマイグレーションを実行
if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
    echo "マイグレーションファイルが見つかりました。実行します..."
    python -c "
from app.database import engine, Base
from app.models import user, category, expense, receipt
import os

# テーブルを作成
Base.metadata.create_all(bind=engine)
print('データベーステーブルを作成/更新しました')

# Alembicマイグレーションを手動で実行
from alembic import context
from alembic.config import Config
from alembic import command
from sqlalchemy import text

# マイグレーションを実行
try:
    # product_nameカラムが存在するか確認
    with engine.connect() as conn:
        result = conn.execute(text(\"\"\"
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='expenses' AND column_name='product_name'
        \"\"\"))
        if not result.fetchone():
            print('product_nameカラムが存在しません。追加します...')
            # カラムを追加
            conn.execute(text('ALTER TABLE expenses ADD COLUMN product_name VARCHAR(200)'))
            # 既存データにデフォルト値を設定
            conn.execute(text(\"\"\"
                UPDATE expenses
                SET product_name = COALESCE(NULLIF(description, ''), '商品')
                WHERE product_name IS NULL
            \"\"\"))
            # NOT NULL制約を追加
            conn.execute(text('ALTER TABLE expenses ALTER COLUMN product_name SET NOT NULL'))
            conn.commit()
            print('product_nameカラムを追加しました')
        else:
            print('product_nameカラムは既に存在します')
except Exception as e:
    print(f'マイグレーション実行中にエラーが発生しました: {e}')
    print('続行します...')
"
else
    echo "マイグレーションファイルがありません。スキップします。"
fi
cd ..

# バックエンドサーバーの起動
echo -e "${GREEN}バックエンドサーバーを起動しています...${NC}"
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Celeryワーカーの起動
echo -e "${GREEN}Celeryワーカーを起動しています...${NC}"
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!
cd ..

# フロントエンドサーバーの起動
echo -e "${GREEN}フロントエンドサーバーを起動しています...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo -e "${GREEN}起動完了！${NC}"
echo "========================================"
echo "バックエンド: http://localhost:8000"
echo "フロントエンド: http://localhost:5173"
echo "API ドキュメント: http://localhost:8000/docs"
echo ""
echo "停止する場合は Ctrl+C を押してください"
echo "========================================"

# シグナルハンドラー
trap "echo ''; echo 'サーバーを停止しています...'; kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# プロセスが終了するまで待機
wait
