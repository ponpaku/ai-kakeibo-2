@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo AI家計簿 起動スクリプト
echo ========================================

REM 環境変数ファイルのチェック
if not exist .env (
    echo 警告: .envファイルが見つかりません
    echo サンプルファイルからコピーしています...
    copy .env.example .env
    echo 重要: .envファイルを編集してDB接続情報などを設定してください
    echo 設定後、このスクリプトを再実行してください
    pause
    exit /b 1
)

REM Python venv環境のチェックと作成
if not exist backend\venv (
    echo Python仮想環境を作成しています...
    cd backend
    python -m venv venv
    cd ..
)

REM バックエンドの依存関係インストール
echo バックエンドの依存関係をインストールしています...
cd backend
call venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..

REM フロントエンドの依存関係インストール
if not exist frontend\node_modules (
    echo フロントエンドの依存関係をインストールしています...
    cd frontend
    call npm install
    cd ..
)

REM アップロードディレクトリの作成
if not exist uploads\receipts mkdir uploads\receipts

REM Redisの起動確認メッセージ
echo.
echo ========================================
echo 重要: 以下を確認してください
echo ========================================
echo 1. Redisサーバーが起動していること
echo 2. MariaDBサーバーが起動していること
echo 3. .envファイルに正しい接続情報が設定されていること
echo.
echo 準備ができたらEnterキーを押してください...
pause >nul

REM 新しいコマンドプロンプトウィンドウでバックエンドサーバーを起動
echo バックエンドサーバーを起動しています...
start "AI家計簿 - バックエンド" cmd /k "cd backend && venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM 新しいコマンドプロンプトウィンドウでCeleryワーカーを起動
echo Celeryワーカーを起動しています...
start "AI家計簿 - Celery" cmd /k "cd backend && venv\Scripts\activate.bat && celery -A app.tasks.celery_app worker --loglevel=info"

REM 新しいコマンドプロンプトウィンドウでフロントエンドサーバーを起動
echo フロントエンドサーバーを起動しています...
start "AI家計簿 - フロントエンド" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo 起動完了！
echo ========================================
echo バックエンド: http://localhost:8000
echo フロントエンド: http://localhost:5173
echo API ドキュメント: http://localhost:8000/docs
echo.
echo 各ウィンドウを閉じるとサーバーが停止します
echo ========================================
echo.
pause
