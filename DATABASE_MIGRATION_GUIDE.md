# データベース移行ガイド

## ⚠️ 重要な変更

このバージョンでは、データモデルの大規模な変更が行われました：

- **旧**: `Expense = 1商品 + 1カテゴリ`
- **新**: `Expense = 決済ヘッダ` + `ExpenseItem[] = 商品明細(カテゴリ付き)`

**既存のデータベースとは互換性がありません。** データベースを削除して再作成する必要があります。

## データベース再作成手順

### 1. バックエンドの環境を有効化

```bash
cd backend
# venvまたはuvの環境を有効化
source venv/bin/activate  # または適切な環境アクティベーション
```

### 2. データベースを削除して再作成

```bash
# データベース再作成スクリプト実行
python recreate_db.py

# 「yes」を入力して確認
```

### 3. 初期データを投入

```bash
# カテゴリ、管理ユーザー、AI設定を作成
python seed_initial_data.py
```

### 4. 完了確認

スクリプト実行後、以下の情報が表示されます：

```
📝 ログイン情報:
   - ユーザー名: admin
   - パスワード: admin123
   - URL: http://localhost:5173
```

### 5. バックエンドを起動

```bash
python -m uvicorn app.main:app --reload
```

## 主な変更点

### Expense モデル
- **削除**: `product_name`, `category_id`, `amount`, `ocr_raw_text`, `expense_date`
- **追加**: `occurred_at`, `merchant_name`, `title`, `total_amount`, `payment_method`, `card_brand`, `card_last4`, ポイント関連フィールド

### ExpenseItem モデル (新規)
- 商品明細を管理
- フィールド: `product_name`, `quantity`, `unit_price`, `line_total`, `category_id`, `category_source`
- **カテゴリ集計の正** (source of truth for category aggregations)

### Receipt モデル
- **追加**: `ocr_raw_output`, `ocr_engine`, `ocr_model`, `schema_version`

### Category モデル
- リレーション変更: `expenses` → `expense_items`

## トラブルシューティング

### データベース接続エラー
`.env`ファイルが正しく設定されているか確認してください：

```env
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=ai_kakeibo
DB_HOST=localhost
DB_PORT=3306
```

### テーブル作成エラー
MySQLサーバーが起動しているか確認してください：

```bash
# MySQL起動確認
mysql -u root -p -e "SELECT 1"
```

### 権限エラー
MySQLユーザーにデータベース作成権限があるか確認してください：

```sql
GRANT ALL PRIVILEGES ON *.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```
