# ワンライナーインストールガイド

requirements.txtを使わずに、すべての依存関係を一度にインストールできるワンライナーコマンド集です。

## Python依存関係のワンライナーインストール

### Linux / Mac

```bash
cd backend && python3 -m venv venv && source venv/bin/activate && pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0 && python init_db.py && cd ..
```

### Windows (PowerShell)

```powershell
cd backend; python -m venv venv; .\venv\Scripts\activate; pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0; python init_db.py; cd ..
```

### Windows (Command Prompt)

```bat
cd backend && python -m venv venv && venv\Scripts\activate.bat && pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0 && python init_db.py && cd ..
```

## 分割版（より読みやすい）

長いワンライナーが見づらい場合は、以下のように分割して実行できます：

### Linux / Mac

```bash
# 1. 仮想環境の作成と有効化
cd backend
python3 -m venv venv
source venv/bin/activate

# 2. 依存関係のインストール（ワンライナー）
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0

# 3. データベース初期化
python init_db.py

# 4. プロジェクトルートに戻る
cd ..
```

### Windows

```bat
REM 1. 仮想環境の作成と有効化
cd backend
python -m venv venv
venv\Scripts\activate.bat

REM 2. 依存関係のインストール（ワンライナー）
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0

REM 3. データベース初期化
python init_db.py

REM 4. プロジェクトルートに戻る
cd ..
```

## フロントエンド依存関係のワンライナー

### すべてのプラットフォーム

```bash
cd frontend && npm install && cd ..
```

## 完全セットアップワンライナー

バックエンド、フロントエンドの両方を一度にセットアップ：

### Linux / Mac

```bash
cd backend && python3 -m venv venv && source venv/bin/activate && pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0 && python init_db.py && deactivate && cd ../frontend && npm install && cd ..
```

### Windows (PowerShell)

```powershell
cd backend; python -m venv venv; .\venv\Scripts\activate; pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 sqlalchemy==2.0.25 pymysql==1.1.0 cryptography==42.0.0 python-multipart==0.0.6 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-dotenv==1.0.0 celery==5.3.6 redis==5.0.1 pillow==10.2.0 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 yomitoku==0.3.0; python init_db.py; deactivate; cd ..\frontend; npm install; cd ..
```

## パッケージ一覧

インストールされるパッケージ：

| パッケージ | バージョン | 用途 |
|-----------|----------|------|
| fastapi | 0.109.0 | Webフレームワーク |
| uvicorn[standard] | 0.27.0 | ASGIサーバー |
| sqlalchemy | 2.0.25 | ORM |
| pymysql | 1.1.0 | MySQLドライバ |
| cryptography | 42.0.0 | 暗号化ライブラリ |
| python-multipart | 0.0.6 | ファイルアップロード |
| python-jose[cryptography] | 3.3.0 | JWT処理 |
| passlib[bcrypt] | 1.7.4 | パスワードハッシュ化 |
| python-dotenv | 1.0.0 | 環境変数管理 |
| celery | 5.3.6 | 非同期タスクキュー |
| redis | 5.0.1 | Redisクライアント |
| pillow | 10.2.0 | 画像処理 |
| pydantic | 2.5.3 | データ検証 |
| pydantic-settings | 2.1.0 | 設定管理 |
| alembic | 1.13.1 | DBマイグレーション |
| yomitoku | 0.3.0 | OCRライブラリ |

## 注意事項

1. **実行前の確認**:
   - Python 3.9以上がインストールされていること
   - Node.js 18以上がインストールされていること
   - MariaDBが起動していること
   - Redisが起動していること
   - `.env`ファイルが設定されていること

2. **エラーが発生した場合**:
   - ネットワーク接続を確認
   - Pythonのバージョンを確認: `python --version` または `python3 --version`
   - pipを最新化: `pip install --upgrade pip`
   - 個別にパッケージをインストールしてエラー箇所を特定

3. **推奨事項**:
   - 初回は分割版を使用して、各ステップでエラーが出ないか確認することを推奨します
   - YomiTokuは初回実行時にモデルをダウンロードするため、時間がかかる場合があります

## トラブルシューティング

### `python3`コマンドが見つからない（Windows）

Windowsでは`python3`の代わりに`python`を使用してください。

### インストールが非常に遅い

中国などネットワーク制限がある地域では、以下のミラーを使用：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi==0.109.0 ...
```

### パーミッションエラー

sudoを使わずに、ユーザー領域にインストール：

```bash
pip install --user fastapi==0.109.0 ...
```

ただし、venv環境を使用している場合は不要です。
