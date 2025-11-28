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

export interface Expense {
  id: number;
  user_id: number;
  category_id?: number;
  amount: number;
  expense_date: string;
  store_name?: string;
  description?: string;
  note?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  ai_confidence?: number;
  created_at: string;
  updated_at?: string;
  category_name?: string;
  receipt?: Receipt;
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
