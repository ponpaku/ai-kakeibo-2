# セットアップガイド

このドキュメントでは、AI家計簿アプリケーションのセットアップ手順を詳しく説明します。

## 目次

1. [前提条件](#前提条件)
2. [依存ソフトウェアのインストール](#依存ソフトウェアのインストール)
3. [アプリケーションのセットアップ](#アプリケーションのセットアップ)
4. [初回起動](#初回起動)
5. [トラブルシューティング](#トラブルシューティング)

## 前提条件

以下のソフトウェアがインストールされている必要があります：

- Python 3.9以上
- Node.js 18以上
- MariaDB 10.5以上
- **Redis 6.0以上（必須）** - バックグラウンドタスク処理に使用
- Claude CLI

⚠️ **重要**: Redisはこのアプリケーションの動作に必須です。OCR処理とAI分類をバックグラウンドで実行するために使用されます。

## 依存ソフトウェアのインストール

### 1. Python

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Mac
```bash
brew install python@3.9
```

#### Windows
[Python公式サイト](https://www.python.org/downloads/)からインストーラーをダウンロードしてインストール

### 2. Node.js

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### Mac
```bash
brew install node@18
```

#### Windows
[Node.js公式サイト](https://nodejs.org/)からインストーラーをダウンロードしてインストール

### 3. MariaDB

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install mariadb-server
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo mysql_secure_installation
```

#### Mac
```bash
brew install mariadb
brew services start mariadb
```

#### Windows
[MariaDB公式サイト](https://mariadb.org/download/)からインストーラーをダウンロードしてインストール

### 4. Redis（必須コンポーネント）

#### Redisが必須である理由

このアプリケーションでは、**Redisは必須**です：

1. **バックグラウンドタスク処理**: YomiToku OCRとClaude AI分類は処理に時間がかかるため、非同期処理が必要です
2. **ユーザー体験の向上**: 「あとは任せる」機能で即座にレスポンスを返し、裏で処理を継続できます
3. **システムの安定性**: Celeryを使用した非同期タスクキューにより、Webサーバーに負荷をかけません
4. **処理の信頼性**: タスクキューにより、処理の失敗時の再試行が可能です

#### インストール方法

##### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis  # 自動起動を有効化
```

##### Linux (CentOS/RHEL)
```bash
sudo yum install redis
# または
sudo dnf install redis
sudo systemctl start redis
sudo systemctl enable redis
```

##### Mac
```bash
brew install redis
brew services start redis
```

##### Windows

Windows版の公式Redisは存在しません。以下の選択肢から選んでください：

**選択肢1: Memurai（推奨）**
- Redis互換のWindows用実装
- https://www.memurai.com/ からダウンロード
- インストール後、自動的にサービスとして起動
- 設定変更不要で使用可能

**選択肢2: WSL2でLinux版Redisを使用**
```bash
# WSL2のUbuntu内で実行
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**選択肢3: Docker Desktop**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

#### Redisの動作確認

インストール後、以下のコマンドで接続を確認します：

```bash
redis-cli ping
```

`PONG`と返答があればRedisは正常に動作しています。

#### Redis設定（オプション）

デフォルト設定で動作しますが、以下の設定を推奨します：

```bash
# Linux
sudo nano /etc/redis/redis.conf

# Mac (Homebrewでインストールした場合)
nano /opt/homebrew/etc/redis.conf
```

推奨設定：
```conf
# メモリ使用量の上限を設定
maxmemory 256mb

# メモリが満杯になった際の削除ポリシー
maxmemory-policy allkeys-lru

# セキュリティ: ローカルホストのみからの接続を許可
bind 127.0.0.1 ::1

# パスワード保護（本番環境では推奨）
# requirepass your_secure_password
```

設定変更後、Redisを再起動：
```bash
# Linux
sudo systemctl restart redis

# Mac
brew services restart redis
```

### 5. Claude CLI

```bash
# インストール方法は環境によって異なります
# 詳細はClaude CLIの公式ドキュメントを参照
```

## アプリケーションのセットアップ

### 1. プロジェクトディレクトリに移動

```bash
cd AI-kakeibo-claude
```

### 2. 環境変数ファイルの作成（重要）

⚠️ **この手順は必須です。後続のステップで`.env`ファイルが必要になります。**

```bash
cp .env.example .env
```

### 3. 環境変数の編集（重要）

`.env`ファイルを開いて、以下の**必須項目**を編集します：

#### 必須設定項目

これらを設定しないと、アプリケーションが起動しません：

```env
# ⚠️ 必須: MariaDBのユーザー名とパスワード
DB_USER=your_db_user          # ← 実際のMariaDBユーザー名に変更
DB_PASSWORD=your_db_password  # ← 実際のMariaDBパスワードに変更

# ⚠️ 必須: セキュリティ用のランダムな文字列
SECRET_KEY=your-secret-key-here  # ← ランダムな文字列に変更（下記参照）
```

**SECRET_KEYの生成方法：**

```bash
# 方法1: Pythonで生成（推奨）
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2: OpenSSLで生成
openssl rand -hex 32

# 方法3: 手動で32文字以上のランダムな文字列を入力
```

#### その他の設定項目（デフォルトで動作します）

必要に応じて変更してください：

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_kakeibo

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# File Upload
UPLOAD_DIR=./uploads/receipts
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp

# OCR Configuration
OCR_MAX_WORKERS=2

# AI Configuration
CLAUDE_CLI_PATH=claude
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Application
BACKEND_PORT=8000
FRONTEND_PORT=5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. データベースの作成

MariaDBにログインしてデータベースを作成：

```bash
mysql -u root -p
```

```sql
CREATE DATABASE ai_kakeibo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ai_kakeibo_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ai_kakeibo.* TO 'ai_kakeibo_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Pythonの依存関係インストール

**推奨方法: requirements.txtを使用（最新版対応）**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
pip install --upgrade pip  # pipを最新版に更新
pip install -r requirements.txt
pip install yomitoku  # OCRライブラリは別途インストール
cd ..
```

この方法を使用することで：
- ✅ 最新の安定版パッケージがインストールされます
- ✅ セキュリティアップデートが適用されます
- ✅ 将来的なメンテナンスが容易になります

> **📝 注意**: YomiToku（OCRライブラリ）はrequirements.txtではなく、個別に`pip install yomitoku`でインストールしてください。

**Windows版:**

```bat
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pip install yomitoku
cd ..
```

> **💡 注意**: 古いバージョンのワンライナーインストール方法は[INSTALL_ONELINER.md](INSTALL_ONELINER.md)に記載されていますが、継続的な運用には推奨されません。最新版対応のためrequirements.txtを使用してください。

### 6. Node.jsの依存関係インストール

```bash
cd frontend
npm install
cd ..
```

### 7. データベースの初期化

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
python init_db.py
cd ..
```

このスクリプトは以下を自動的に実行します：
- データベーステーブルの作成
- 管理者ユーザーの作成（ユーザー名: admin, パスワード: admin123）
- 初期カテゴリの作成

## 初回起動

### 起動前の確認事項

アプリケーションを起動する前に、以下を確認してください：

1. **MariaDBが起動していること**
   ```bash
   # Linux
   sudo systemctl status mariadb

   # Mac
   brew services list | grep mariadb
   ```

2. **Redisが起動していること（必須）**
   ```bash
   redis-cli ping
   # PONGと返答があればOK
   ```

   起動していない場合：
   ```bash
   # Linux
   sudo systemctl start redis

   # Mac
   brew services start redis

   # Windows (Memurai)
   # サービスが自動起動しているはず

   # Docker
   docker start redis
   ```

3. **`.env`ファイルが正しく設定されていること**
   - DB接続情報
   - Redis接続情報（デフォルトで問題ない場合が多い）
   - SECRET_KEYの設定

### アプリケーションの起動

#### Linux/Mac

```bash
./run.sh
```

#### Windows

```bat
run.bat
```

起動スクリプトは以下を自動的に実行します：
1. Python仮想環境の作成（未作成の場合）
2. 依存関係のインストール（未インストールの場合）
3. バックエンドサーバーの起動（FastAPI）
4. **Celeryワーカーの起動**（バックグラウンドタスク処理）
5. フロントエンドサーバーの起動（Vite）

起動したら、以下のURLにアクセス：

- **フロントエンド**: http://localhost:5173
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

**外部IPからのアクセス**:
- フロントエンド: `http://{server-ip}:5173`
- バックエンドAPI: `http://{server-ip}:8000`
- Viteは`0.0.0.0`でリッスンするため、同じネットワーク内の他のデバイスからアクセス可能です

初期ログイン情報：
- **ユーザー名**: admin
- **パスワード**: admin123

⚠️ **重要**: 初回ログイン後、必ずパスワードを変更してください！

### 動作確認

1. ログイン画面が表示されることを確認
2. 管理者アカウントでログイン
3. ダッシュボードが表示されることを確認
4. 「入力」画面で手入力を試してみる
5. レシート撮影（OCRとAI分類）をテストする

## トラブルシューティング

### .envファイル関連のエラー

**症状**: `python init_db.py`実行時に以下のようなエラーが出る
```
ValidationError: 3 validation errors for Settings
DB_USER
  Field required [type=missing, ...]
DB_PASSWORD
  Field required [type=missing, ...]
SECRET_KEY
  Field required [type=missing, ...]
```

**原因**: `.env`ファイルが存在しないか、必須フィールドが設定されていません。

**解決方法**:

修正された`init_db.py`を使用している場合、わかりやすいエラーメッセージが表示されます。指示に従ってください。

手動で確認する場合：

1. プロジェクトルートに`.env`ファイルが存在するか確認：
```bash
cd /path/to/AI-kakeibo-claude
ls -la .env
```

2. 存在しない場合は作成：
```bash
cp .env.example .env
```

3. `.env`ファイルを編集して必須項目を設定：
```bash
nano .env  # または vim、code、notepad など
```

必須項目（必ず設定してください）：
```env
DB_USER=your_actual_db_user        # 実際のMariaDBユーザー名
DB_PASSWORD=your_actual_password   # 実際のMariaDBパスワード
SECRET_KEY=random_string_here      # ランダムな文字列
```

4. SECRET_KEYの生成：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. 保存して再実行：
```bash
cd backend
source venv/bin/activate
python init_db.py
```

### ポートが既に使用されている

別のアプリケーションがポート8000または5173を使用している場合、`.env`ファイルで別のポートを指定できます：

```env
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

### MariaDB接続エラー

1. MariaDBが起動しているか確認：
```bash
sudo systemctl status mariadb  # Linux
brew services list              # Mac
```

2. `.env`ファイルの接続情報が正しいか確認

3. データベースとユーザーが作成されているか確認：
```bash
mysql -u your_user -p -e "SHOW DATABASES;"
```

### Redis接続エラー

**症状**: `Connection refused` や `Error connecting to Redis` などのエラー

Redisはアプリケーションの動作に**必須**です。以下の手順で問題を解決してください。

#### 1. Redisが起動していない

確認方法：
```bash
redis-cli ping
```

- `PONG`と返答がない場合、Redisが起動していません

起動方法：
```bash
# Linux
sudo systemctl start redis
sudo systemctl status redis  # 状態確認
sudo systemctl enable redis  # 自動起動を有効化

# Mac
brew services start redis
brew services list           # 状態確認

# Docker
docker start redis
# または新規コンテナを作成
docker run -d -p 6379:6379 --name redis redis:latest
```

#### 2. Redisがインストールされていない

確認方法：
```bash
redis-cli --version
```

コマンドが見つからない場合は、上記「Redis（必須コンポーネント）」セクションを参照してインストールしてください。

#### 3. ポートが競合している

他のプログラムがポート6379を使用している可能性があります。

確認方法：
```bash
# Linux/Mac
sudo lsof -i :6379
# または
sudo netstat -tuln | grep 6379

# Windows
netstat -ano | findstr :6379
```

解決方法：
- 競合しているプログラムを停止
- または、`.env`ファイルで別のポートを指定：
```env
REDIS_PORT=6380
```

Redis側も設定変更が必要：
```bash
# Linux
sudo nano /etc/redis/redis.conf
# port 6379 を port 6380 に変更

# 再起動
sudo systemctl restart redis
```

#### 4. Celeryワーカーが起動していない

Redisは起動しているが、バックグラウンドタスクが処理されない場合：

手動でCeleryを起動してエラーメッセージを確認：
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
celery -A app.tasks.celery_app worker --loglevel=info
```

#### 5. Windows環境での特別な対処

Windows版の公式Redisは存在しないため、以下のいずれかを使用してください：

**推奨: Memurai**
1. https://www.memurai.com/ からダウンロード
2. インストーラーを実行
3. 自動的にサービスとして起動
4. Redis互換なので設定変更不要

**代替案: WSL2**
```bash
# WSL2のUbuntu内で
sudo service redis-server start
sudo service redis-server status
```

**代替案: Docker Desktop**
```bash
docker run -d -p 6379:6379 --restart always --name redis redis:latest
```

#### デバッグ方法

Redisの状態を確認：
```bash
redis-cli info              # サーバー情報を表示
redis-cli client list       # 接続しているクライアント一覧
redis-cli config get port   # 使用しているポートを確認
redis-cli monitor           # リアルタイムでコマンドを監視（Ctrl+Cで終了）
```

Redisのログを確認：
```bash
# Linux
sudo journalctl -u redis -n 50  # 最新50行のログを表示

# Mac
tail -f /opt/homebrew/var/log/redis.log
```

### YomiToku OCRエラー

初回実行時、YomiTokuはモデルファイルをダウンロードします。これには時間がかかる場合があります。

エラーが続く場合：
```bash
cd backend
source venv/bin/activate
pip uninstall yomitoku
pip install yomitoku
```

### Claude CLI エラー

Claude CLIが正しくインストールされているか確認：
```bash
claude --version
```

パスが通っていない場合、`.env`ファイルで絶対パスを指定：
```env
CLAUDE_CLI_PATH=/path/to/claude
```

### パーミッションエラー（Linux/Mac）

アップロードディレクトリのパーミッションを確認：
```bash
chmod -R 755 uploads/
```

### 起動スクリプトが実行できない（Linux/Mac）

実行権限を付与：
```bash
chmod +x run.sh
```

## 次のステップ

セットアップが完了したら、[README.md](README.md)の「使い方」セクションを参照して、アプリケーションの使用を開始してください。
