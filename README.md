# AI家計簿

AIを活用した家計簿Webアプリケーション

## 概要

ADHD夫婦でも継続できる家計簿を目指して開発されたアプリケーションです。
レシート撮影による自動入力と、AIによる自動分類により、家計簿をつける手間を大幅に削減します。

## 主な機能

- **レシート撮影による自動入力**: YomiToku OCRでレシートを自動認識
- **AI自動分類**: Claude AIが出費を適切なカテゴリに自動分類
- **手入力サポート**: 電卓機能付きの簡単入力
- **ダッシュボード**: 収支が一目でわかる「みらいまる見え政治資金」風のUI
- **管理機能**: ユーザー管理、カテゴリ管理

## 技術スタック

### バックエンド
- **FastAPI**: Pythonの高速Webフレームワーク
- **SQLAlchemy**: ORM
- **MariaDB**: データベース
- **Celery + Redis**: バックグラウンドタスク処理
- **YomiToku**: OCRライブラリ
- **Claude CLI**: AI分類

### フロントエンド
- **React**: UIライブラリ
- **TypeScript**: 型安全性
- **Vite**: ビルドツール
- **Tailwind CSS**: スタイリング
- **Recharts**: グラフ表示

## システム要件

- Python 3.9以上
- Node.js 18以上
- MariaDB 10.5以上
- **Redis 6.0以上（必須）** - バックグラウンドタスク処理に使用
- Claude CLI（インストール済み）

⚠️ **重要**: Redisはアプリケーションの動作に必須です。インストールと起動を忘れないでください。

## セットアップ

### 1. リポジトリのクローンまたはダウンロード

```bash
cd AI-kakeibo-claude
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の項目を設定してください：

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=ai_kakeibo

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=ランダムな文字列を生成してください

# AI Configuration
CLAUDE_CLI_PATH=claude
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### 3. データベースの作成

MariaDBにログインして、データベースを作成してください：

```sql
CREATE DATABASE ai_kakeibo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Redisのセットアップ（必須）

#### Redisが必須である理由

このアプリケーションでは、**Redisは必須コンポーネント**です。以下の理由により不可欠です：

1. **バックグラウンドタスク処理**: YomiToku OCRによるレシート認識とClaude AIによる分類処理は、それぞれ数秒～数十秒かかる場合があります。これらを同期的に処理するとHTTPリクエストがタイムアウトする可能性があります。

2. **ユーザー体験の向上**: 「あとは任せる」ボタンを押すと即座にレスポンスが返り、バックグラウンドで処理が続行されます。これによりユーザーは待機する必要がありません。

3. **システムの安定性**: Celeryを使用した非同期タスクキューにより、重い処理がWebサーバーに負荷をかけることを防ぎます。

4. **処理の信頼性**: タスクキューにより、処理の失敗時の再試行や、処理状況の追跡が可能になります。

#### インストール方法

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install redis-server
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install redis
# または
sudo dnf install redis
```

**Mac:**
```bash
brew install redis
```

**Windows:**
Windowsには公式のRedisがありませんが、以下の選択肢があります：
- **Memurai** (推奨): https://www.memurai.com/
- **Redis on WSL**: WSL2でLinux版Redisを使用
- **Docker**: Docker Desktop経由でRedisコンテナを使用

#### Redisの起動

**Linux (Ubuntu/Debian):**
```bash
sudo systemctl start redis
sudo systemctl enable redis  # 自動起動を有効化
```

**Linux (CentOS/RHEL):**
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

**Mac:**
```bash
brew services start redis
```

**Windows (Memurai):**
- インストーラーで自動的にサービスとして起動します

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

#### Redisの動作確認

以下のコマンドで接続を確認します：

```bash
redis-cli ping
```

`PONG`と返答があればRedisは正常に動作しています。

#### Redis設定（オプション）

デフォルト設定で動作しますが、本番環境では以下の設定を推奨します：

```bash
sudo nano /etc/redis/redis.conf  # Linuxの場合
```

推奨設定：
- `maxmemory 256mb` - メモリ使用量の上限を設定
- `maxmemory-policy allkeys-lru` - メモリが満杯になった際の削除ポリシー
- `bind 127.0.0.1 ::1` - ローカルホストのみからの接続を許可（セキュリティ）

設定変更後、Redisを再起動：
```bash
sudo systemctl restart redis  # Linux
brew services restart redis   # Mac
```

### 5. 依存関係のインストールとDB初期化

**簡単な方法（推奨）:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
python init_db.py  # データベース初期化（ユーザーとカテゴリを自動作成）
cd ..
```

`init_db.py`は以下を自動的に実行します：
- データベーステーブルの作成
- 管理者ユーザーの作成（ユーザー名: admin, パスワード: admin123）
- 初期カテゴリ（食費、日用品、交通費など）の作成

フロントエンドの依存関係もインストール：

```bash
cd frontend
npm install
cd ..
```

**手動でユーザーとカテゴリを作成する場合:**

<details>
<summary>展開して手順を確認</summary>

Pythonコンソールから手動で作成することもできます：

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
python
```

```python
from app.database import SessionLocal
from app.models.user import User
from app.models.category import Category
from app.utils.security import get_password_hash

db = SessionLocal()

# 管理者ユーザーを作成
admin = User(
    username="admin",
    email="admin@example.com",
    full_name="管理者",
    hashed_password=get_password_hash("admin123"),
    is_admin=True,
    is_active=True
)
db.add(admin)

# カテゴリを作成
categories = [
    Category(name="食費", description="食材、外食など", color="#EF4444", sort_order=1),
    Category(name="日用品", description="生活必需品", color="#F59E0B", sort_order=2),
    Category(name="交通費", description="電車、バス、ガソリン代", color="#10B981", sort_order=3),
    Category(name="娯楽", description="趣味、レジャー", color="#3B82F6", sort_order=4),
    Category(name="医療費", description="病院、薬代", color="#8B5CF6", sort_order=5),
    Category(name="その他", description="その他の支出", color="#6B7280", sort_order=6),
]

for cat in categories:
    db.add(cat)

db.commit()
print("初期データを作成しました")
```

</details>

## 起動方法

**起動前の確認事項:**
- ✅ MariaDBが起動していること
- ✅ **Redisが起動していること（必須）**
- ✅ `.env`ファイルが正しく設定されていること

Redisの起動確認：
```bash
redis-cli ping
# PONGと返答があればOK
```

### Linux/Mac
```bash
./run.sh
```

### Windows
```bat
run.bat
```

起動スクリプトは以下を自動的に実行します：
1. Python仮想環境の作成（未作成の場合）
2. 依存関係のインストール（未インストールの場合）
3. バックエンドサーバーの起動（FastAPI）
4. Celeryワーカーの起動（バックグラウンドタスク処理）
5. フロントエンドサーバーの起動（Vite）

起動後、以下のURLでアクセスできます：

- **フロントエンド**: http://localhost:5173
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

初期ログイン情報：
- ユーザー名: `admin`
- パスワード: `admin123`

⚠️ **重要**: 初回ログイン後、必ずパスワードを変更してください！

## 使い方

### 1. ログイン

初期ユーザー（上記で作成したユーザー）でログインします。

### 2. レシート入力

1. 「入力」画面を開く
2. 「レシート撮影」を選択
3. レシート画像を撮影またはアップロード
4. 「OCR実行」で結果を確認してから送信、または「あとは任せる」で自動処理

### 3. 手入力

1. 「入力」画面を開く
2. 「手入力」を選択
3. 金額、日付、店舗名などを入力
4. 必要に応じて電卓機能を使用
5. カテゴリを選択するか、AIに分類させる

### 4. ダッシュボード

- ホーム画面で今月の収支を確認
- カテゴリ別の円グラフで支出の内訳を表示
- 最近の出費一覧から詳細を確認・編集

### 5. 管理画面

管理者権限を持つユーザーは以下の操作が可能です：

- ユーザーの追加・編集・削除
- カテゴリの追加・編集・削除

## トラブルシューティング

### OCRが動作しない

YomiTokuは初回実行時にモデルをダウンロードします。時間がかかる場合があります。

### AI分類が動作しない

Claude CLIが正しくインストールされているか確認してください：

```bash
claude --version
```

### データベース接続エラー

`.env`ファイルのDB接続情報が正しいか確認してください。
また、MariaDBサーバーが起動しているか確認してください。

### Redisエラー

**症状**: `Connection refused` や `Error connecting to Redis` などのエラー

**原因と解決方法:**

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

# Mac
brew services start redis
brew services list           # 状態確認

# Docker
docker start redis
# または
docker run -d -p 6379:6379 --name redis redis:latest
```

#### 2. ポートが競合している

他のプログラムがポート6379を使用している可能性があります。

確認方法：
```bash
# Linux/Mac
sudo lsof -i :6379
# または
sudo netstat -tuln | grep 6379
```

解決方法：
- 競合しているプログラムを停止
- または、`.env`ファイルで別のポートを指定：
```env
REDIS_PORT=6380
```

#### 3. Redisがインストールされていない

確認方法：
```bash
redis-cli --version
```

コマンドが見つからない場合は、上記「Redisのセットアップ」セクションを参照してインストールしてください。

#### 4. Celeryワーカーが起動していない

Redisは起動しているが、バックグラウンドタスクが処理されない場合：

```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

エラーメッセージを確認して対処してください。

#### 5. Windows環境でのRedis問題

Windows版Redisは公式サポートされていません。以下の代替案を使用してください：

**推奨: Memurai**
- https://www.memurai.com/ からダウンロード
- インストール後、自動的にサービスとして起動
- Redis互換なので設定変更不要

**代替案1: WSL2**
```bash
# WSL2内で
sudo apt install redis-server
sudo service redis-server start
```

**代替案2: Docker Desktop**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

#### 6. Redisの再起動

問題が解決しない場合、Redisを再起動してみてください：

```bash
# Linux
sudo systemctl restart redis

# Mac
brew services restart redis

# Docker
docker restart redis
```

#### デバッグ用コマンド

Redisの状態を確認：
```bash
redis-cli info
redis-cli client list
redis-cli monitor  # リアルタイムでコマンドを監視（Ctrl+Cで終了）
```

## プロジェクト構造

```
AI-kakeibo-claude/
├── backend/              # バックエンド（FastAPI）
│   ├── app/
│   │   ├── api/         # APIエンドポイント
│   │   ├── models/      # データベースモデル
│   │   ├── schemas/     # Pydanticスキーマ
│   │   ├── services/    # ビジネスロジック
│   │   ├── tasks/       # Celeryタスク
│   │   └── utils/       # ユーティリティ
│   └── requirements.txt
├── frontend/            # フロントエンド（React + TypeScript）
│   ├── src/
│   │   ├── components/  # Reactコンポーネント
│   │   ├── pages/       # ページコンポーネント
│   │   ├── services/    # API通信
│   │   └── types/       # 型定義
│   └── package.json
├── uploads/             # アップロードされた画像
├── run.sh              # 起動スクリプト（Linux/Mac）
├── run.bat             # 起動スクリプト（Windows）
└── README.md           # このファイル
```

## ライセンス

このプロジェクトは個人利用を目的としています。

## 注意事項

- このアプリケーションは家庭内での利用を目的としています
- セキュリティ上、外部公開する場合は適切な認証・認可の強化が必要です
- レシート画像はファイルシステム上に保存されます。定期的なバックアップを推奨します

## 今後の改善点

- [ ] データエクスポート機能
- [ ] 予算管理機能
- [ ] 月次レポート
- [ ] スマートフォンアプリ化
- [ ] 複数家計の管理

## 開発者向け情報

### 開発モード

バックエンドとフロントエンドを個別に起動する場合：

**バックエンド:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Celery:**
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

**フロントエンド:**
```bash
cd frontend
npm run dev
```

### データベースマイグレーション

Alembicを使用してマイグレーションを管理できます：

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "migration message"
alembic upgrade head
```

## サポート

質問や問題がある場合は、Issueを作成してください。
