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
