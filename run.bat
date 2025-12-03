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

REM 初期ユーザーの確認と作成
echo 初期ユーザーの確認をしています...
cd backend
call venv\Scripts\activate.bat
python -c "from app.database import SessionLocal; from app.models.user import User; from app.models.category import Category; from app.utils.security import get_password_hash; db = SessionLocal(); user_count = db.query(User).count(); print(f'ユーザー: {user_count}件'); admin = User(username='admin', email='admin@example.com', full_name='管理者', hashed_password=get_password_hash('admin123'), is_admin=True, is_active=True) if user_count == 0 else None; db.add(admin) if admin else None; [db.add(Category(name=n, description=d, color=c, icon=i, sort_order=s)) for n, d, c, i, s in [('食費', '食材、外食など', '#EF4444', 'shopping-cart', 1), ('日用品', '生活必需品', '#F59E0B', 'home', 2), ('交通費', '電車、バス、ガソリン代', '#10B981', 'car', 3), ('娯楽', '趣味、レジャー', '#3B82F6', 'music', 4), ('医療費', '病院、薬代', '#8B5CF6', 'heart', 5), ('光熱費', '電気、ガス、水道', '#EC4899', 'zap', 6), ('通信費', 'スマホ、インターネット', '#06B6D4', 'smartphone', 7), ('その他', 'その他の支出', '#6B7280', 'more-horizontal', 99)]] if user_count == 0 and db.query(Category).count() == 0 else None; db.commit() if user_count == 0 else None; print('初期ユーザーとカテゴリを作成しました (admin/admin123)') if user_count == 0 else print('初期化をスキップします'); db.close()"
cd ..

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
