#!/bin/bash

# AI家計簿 セットアップスクリプト (Debian/Ubuntu専用)
# このスクリプトは開発環境をセットアップします

set -e  # エラー時に終了

echo "========================================="
echo " AI家計簿 セットアップスクリプト"
echo " (Debian/Ubuntu専用)"
echo "========================================="
echo ""

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 必須コマンドのチェック
check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 がインストールされています"
        return 0
    else
        print_warning "$1 がインストールされていません"
        return 1
    fi
}

# システムパッケージのインストール
install_system_packages() {
    print_info "システムパッケージのインストールを開始します..."
    print_info "apt-getでパッケージをインストールします（sudo権限が必要です）"

    # パッケージリストの更新
    sudo apt-get update

    # Python関連
    if ! check_command python3; then
        sudo apt-get install -y python3 python3-pip python3-venv
    fi

    # Node.js & npm
    if ! check_command node; then
        print_info "Node.js 18.xをインストールします..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    # MariaDB
    if ! check_command mysql; then
        print_info "MariaDBをインストールしますか? (y/n)"
        read -r install_mariadb
        if [ "$install_mariadb" == "y" ]; then
            sudo apt-get install -y mariadb-server mariadb-client
            sudo systemctl start mariadb
            sudo systemctl enable mariadb
            print_success "MariaDBをインストールしました"
            print_warning "セキュリティ設定のため、sudo mysql_secure_installation を実行してください"
        fi
    fi

    # Redis
    if ! check_command redis-cli; then
        sudo apt-get install -y redis-server
        sudo systemctl start redis
        sudo systemctl enable redis
        print_success "Redisをインストールしました"
    fi

    # その他の必要なパッケージ
    sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev git curl

    print_success "システムパッケージのインストールが完了しました"
}

# システムパッケージのインストールを実行
print_info "システムパッケージをインストールしますか? (y/n)"
print_warning "既にインストール済みの場合は 'n' を選択してください"
read -r install_packages

if [ "$install_packages" == "y" ]; then
    install_system_packages
else
    print_info "システムパッケージのインストールをスキップしました"
fi

echo ""
print_info "必須コマンドの確認..."
check_command python3 || { print_error "Python3が必要です"; exit 1; }
check_command node || { print_error "Node.jsが必要です"; exit 1; }
check_command npm || { print_error "npmが必要です"; exit 1; }
check_command mysql || print_warning "MariaDB/MySQLがインストールされていません"
check_command redis-cli || print_warning "Redisがインストールされていません（必須です！）"

echo ""
print_info "プロジェクトディレクトリを確認中..."
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "プロジェクトルートディレクトリで実行してください"
    exit 1
fi
print_success "プロジェクトディレクトリを確認しました"

# 環境変数ファイルのセットアップ
echo ""
print_info "環境変数ファイルをセットアップします..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env.exampleから.envファイルを作成しました"
        print_warning "重要: .envファイルを編集して以下の項目を設定してください:"
        echo "  - DB_USER: MariaDBのユーザー名"
        echo "  - DB_PASSWORD: MariaDBのパスワード"
        echo "  - SECRET_KEY: ランダムな文字列（以下のコマンドで生成可能）"
        echo "      python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
    else
        print_error ".env.exampleファイルが見つかりません"
        exit 1
    fi
else
    print_success ".envファイルは既に存在します"
fi

# データベースの作成（オプション）
echo ""
print_info "データベースを作成しますか? (y/n)"
print_warning "既に作成済みの場合は 'n' を選択してください"
read -r create_db

if [ "$create_db" == "y" ]; then
    print_info "MariaDBのrootパスワードを入力してください:"
    mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS ai_kakeibo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES LIKE 'ai_kakeibo';
EOF
    if [ $? -eq 0 ]; then
        print_success "データベース 'ai_kakeibo' を作成しました"
    else
        print_error "データベースの作成に失敗しました"
    fi
fi

# Python仮想環境のセットアップ
echo ""
print_info "Python仮想環境をセットアップします..."
cd backend

if [ ! -d "venv" ]; then
    print_info "仮想環境を作成中..."
    python3 -m venv venv
    print_success "仮想環境を作成しました"
else
    print_success "仮想環境は既に存在します"
fi

# 仮想環境を有効化
source venv/bin/activate

# pipを最新版に更新
print_info "pipを更新中..."
pip install --upgrade pip

# Python依存関係のインストール
print_info "Python依存関係をインストール中..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "Python依存関係のインストールが完了しました"
else
    print_error "Python依存関係のインストールに失敗しました"
    deactivate
    cd ..
    exit 1
fi

# データベースの初期化
echo ""
print_info "データベースを初期化しますか? (y/n)"
print_warning "既に初期化済みの場合は 'n' を選択してください"
read -r init_db

if [ "$init_db" == "y" ]; then
    print_info "データベースを初期化中..."
    python init_db.py
    if [ $? -eq 0 ]; then
        print_success "データベースの初期化が完了しました"
        print_info "初期ログイン情報:"
        echo "  ユーザー名: admin"
        echo "  パスワード: admin123"
        print_warning "初回ログイン後、必ずパスワードを変更してください！"
    else
        print_error "データベースの初期化に失敗しました"
        print_warning ".envファイルの設定を確認してください"
    fi
fi

# 仮想環境を無効化
deactivate
cd ..

# フロントエンド依存関係のインストール
echo ""
print_info "フロントエンド依存関係をインストール中..."
cd frontend
npm install

if [ $? -eq 0 ]; then
    print_success "フロントエンド依存関係のインストールが完了しました"
else
    print_error "フロントエンド依存関係のインストールに失敗しました"
    cd ..
    exit 1
fi

cd ..

# アップロードディレクトリの作成
echo ""
print_info "アップロードディレクトリを作成中..."
mkdir -p uploads/receipts
chmod -R 755 uploads
print_success "アップロードディレクトリを作成しました"

# セットアップ完了
echo ""
echo "========================================="
print_success "セットアップが完了しました！"
echo "========================================="
echo ""
print_info "次のステップ:"
echo "1. .envファイルを編集して、必須項目を設定してください"
echo "   - DB_USER, DB_PASSWORD, SECRET_KEY"
echo ""
echo "2. Redisが起動していることを確認してください:"
echo "   redis-cli ping"
echo "   （PONGと返答があればOK）"
echo ""
echo "3. MariaDBが起動していることを確認してください:"
echo "   sudo systemctl status mariadb"
echo ""
echo "4. アプリケーションを起動してください:"
echo "   ./run.sh"
echo ""
echo "5. ブラウザで以下のURLにアクセスしてください:"
echo "   http://localhost:5173"
echo ""
print_warning "注意事項:"
echo "- Codex execは別途セットアップが必要です（ユーザー認証が必要なため）"
echo "- 初回ログイン後、必ずパスワードを変更してください"
echo "- セキュリティのため、外部公開する場合は追加の設定が必要です"
echo ""
print_success "セットアップスクリプトを終了します"
