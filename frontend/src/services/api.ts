import axios from 'axios';
import type { User, Category, Expense, DashboardSummary, LoginResponse } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// トークンをリクエストに追加するインターセプター
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 認証エラーの処理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 認証API
export const authAPI = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// ユーザーAPI
export const userAPI = {
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },
  listUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/users/');
    return response.data;
  },
  createUser: async (data: any): Promise<User> => {
    const response = await api.post<User>('/users/', data);
    return response.data;
  },
  updateUser: async (userId: number, data: any): Promise<User> => {
    const response = await api.put<User>(`/users/${userId}`, data);
    return response.data;
  },
  deleteUser: async (userId: number): Promise<void> => {
    await api.delete(`/users/${userId}`);
  },
};

// カテゴリAPI
export const categoryAPI = {
  listCategories: async (activeOnly = true): Promise<Category[]> => {
    const response = await api.get<Category[]>('/categories/', {
      params: { active_only: activeOnly },
    });
    return response.data;
  },
  getCategory: async (categoryId: number): Promise<Category> => {
    const response = await api.get<Category>(`/categories/${categoryId}`);
    return response.data;
  },
  createCategory: async (data: any): Promise<Category> => {
    const response = await api.post<Category>('/categories/', data);
    return response.data;
  },
  updateCategory: async (categoryId: number, data: any): Promise<Category> => {
    const response = await api.put<Category>(`/categories/${categoryId}`, data);
    return response.data;
  },
  deleteCategory: async (categoryId: number): Promise<void> => {
    await api.delete(`/categories/${categoryId}`);
  },
};

// 出費API
export const expenseAPI = {
  listExpenses: async (params?: any): Promise<{ total: number; expenses: Expense[] }> => {
    const response = await api.get<{ total: number; expenses: Expense[] }>('/expenses/', { params });
    return response.data;
  },
  getExpense: async (expenseId: number): Promise<Expense> => {
    const response = await api.get<Expense>(`/expenses/${expenseId}`);
    return response.data;
  },
  createManualExpense: async (data: any): Promise<Expense> => {
    const response = await api.post<Expense>('/expenses/manual', data);
    return response.data;
  },
  updateExpense: async (expenseId: number, data: any): Promise<Expense> => {
    const response = await api.put<Expense>(`/expenses/${expenseId}`, data);
    return response.data;
  },
  deleteExpense: async (expenseId: number): Promise<void> => {
    await api.delete(`/expenses/${expenseId}`);
  },
  reclassify: async (expenseId: number): Promise<void> => {
    await api.post(`/expenses/${expenseId}/reclassify`);
  },
};

// レシートAPI
export const receiptAPI = {
  uploadReceipt: async (file: File, autoProcess: boolean): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_process', String(autoProcess));
    const response = await api.post('/receipts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  processReceipt: async (expenseId: number, skipAi: boolean): Promise<void> => {
    await api.post(`/receipts/${expenseId}/process`, null, {
      params: { skip_ai: skipAi },
    });
  },
  getReceiptImage: (receiptId: number): string => {
    return `/api/receipts/${receiptId}/image`;
  },
  deleteReceipt: async (receiptId: number): Promise<void> => {
    await api.delete(`/receipts/${receiptId}`);
  },
};

// ダッシュボードAPI
export const dashboardAPI = {
  getSummary: async (startDate?: string, endDate?: string): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>('/dashboard/summary', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },
  getRecentExpenses: async (limit = 10): Promise<Expense[]> => {
    const response = await api.get<Expense[]>('/dashboard/recent-expenses', {
      params: { limit },
    });
    return response.data;
  },
};

export default api;
