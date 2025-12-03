export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
}

// ExpenseItem（商品明細）
export interface ExpenseItem {
  id: number;
  expense_id: number;
  position: number;
  product_name: string;
  quantity?: number;
  unit_price?: number;
  line_total: number;
  category_id?: number;
  category_source?: 'ocr' | 'ai' | 'manual' | 'rule';
  ai_confidence?: number;
  category_name?: string;
}

// Expense（決済ヘッダ）
export interface Expense {
  id: number;
  user_id: number;
  occurred_at: string;  // 発生日時
  merchant_name?: string;  // 店舗名/加盟店名
  title?: string;  // 決済のタイトル
  total_amount: number;  // 合計金額（円）
  currency: string;  // 通貨コード
  payment_method?: string;  // 支払い方法
  card_brand?: string;  // カードブランド
  card_last4?: string;  // カード下4桁
  points_used?: number;  // 使用ポイント
  points_earned?: number;  // 獲得ポイント
  points_program?: string;  // ポイントプログラム名
  description?: string;  // 説明
  note?: string;  // 備考
  status: 'pending' | 'processing' | 'completed' | 'failed';
  ai_confidence?: number;
  created_at: string;
  updated_at?: string;
  receipt?: Receipt;
  items?: ExpenseItem[];  // 商品明細
}

export interface Receipt {
  id: number;
  original_filename?: string;
  file_path: string;
  ocr_processed: boolean;
  created_at: string;
}

export interface DashboardSummary {
  total_expenses: number;
  expense_count: number;
  item_count?: number;  // 商品明細数
  average_expense: number;
  category_breakdown: CategoryBreakdown[];
  daily_expenses: DailyExpense[];
  comparison: {
    previous_month_total: number;
    change_amount: number;
    change_percent: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface CategoryBreakdown {
  category_id: number;
  category_name: string;
  color: string;
  total: number;
  count: number;
  percentage: number;
}

export interface DailyExpense {
  date: string;
  total: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AISettings {
  id: number;
  ocr_model: string;
  ocr_enabled: boolean;
  classification_model: string;
  classification_enabled: boolean;
  sandbox_mode: string;
  skip_git_repo_check: boolean;
  ocr_system_prompt?: string;
  classification_system_prompt?: string;
}

export interface AISettingsUpdate {
  ocr_model: string;
  ocr_enabled: boolean;
  classification_model: string;
  classification_enabled: boolean;
  sandbox_mode: string;
  skip_git_repo_check: boolean;
  ocr_system_prompt?: string;
  classification_system_prompt?: string;
}
