import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import Layout from '@/components/common/Layout';
import Loading from '@/components/common/Loading';
import ExpenseList from '@/components/Dashboard/ExpenseList';
import { dashboardAPI, expenseAPI, receiptAPI, categoryAPI } from '@/services/api';
import type { DashboardSummary, Expense, Category } from '@/types';
import { TrendingUp, TrendingDown, DollarSign, ShoppingBag } from 'lucide-react';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<number | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [editForm, setEditForm] = useState({
    product_name: '',
    amount: 0,
    expense_date: '',
    store_name: '',
    note: '',
    category_id: undefined as number | undefined,
  });

  useEffect(() => {
    loadData();
    loadCategories();
  }, []);

  const loadData = async () => {
    try {
      const [summaryData, expensesData] = await Promise.all([
        dashboardAPI.getSummary(),
        dashboardAPI.getRecentExpenses(10),
      ]);
      setSummary(summaryData);
      setRecentExpenses(expensesData);
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await categoryAPI.listCategories();
      setCategories(data);
    } catch (error) {
      console.error('カテゴリの読み込みに失敗しました:', error);
    }
  };

  const handleEditExpense = (expense: Expense) => {
    setEditingExpense(expense);
    setEditForm({
      product_name: expense.product_name,
      amount: expense.amount,
      expense_date: expense.expense_date.split('T')[0],
      store_name: expense.store_name || '',
      note: expense.note || '',
      category_id: expense.category_id,
    });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingExpense) return;

    try {
      await expenseAPI.updateExpense(editingExpense.id, editForm);
      setEditingExpense(null);
      loadData();
    } catch (error) {
      console.error('更新に失敗しました:', error);
      alert('更新に失敗しました');
    }
  };

  const handleDeleteExpense = async (expenseId: number) => {
    try {
      await expenseAPI.deleteExpense(expenseId);
      loadData();
    } catch (error) {
      console.error('削除に失敗しました:', error);
    }
  };

  const handleViewReceipt = (receiptId: number) => {
    setSelectedReceipt(receiptId);
  };

  if (loading) {
    return (
      <Layout>
        <Loading />
      </Layout>
    );
  }

  if (!summary) {
    return (
      <Layout>
        <div className="text-center text-gray-600">データがありません</div>
      </Layout>
    );
  }

  const isIncrease = summary.comparison.change_percent > 0;

  return (
    <Layout>
      <div className="space-y-6">
        {/* サマリーカード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">今月の支出</p>
                <p className="text-2xl font-bold text-gray-900">
                  ¥{summary.total_expenses.toLocaleString()}
                </p>
              </div>
              <DollarSign className="text-primary-600" size={32} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">支出回数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.expense_count}回
                </p>
              </div>
              <ShoppingBag className="text-primary-600" size={32} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">平均支出</p>
                <p className="text-2xl font-bold text-gray-900">
                  ¥{Math.round(summary.average_expense).toLocaleString()}
                </p>
              </div>
              <DollarSign className="text-primary-600" size={32} />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">先月比</p>
                <p className={`text-2xl font-bold ${isIncrease ? 'text-red-600' : 'text-green-600'}`}>
                  {isIncrease ? '+' : ''}{summary.comparison.change_percent.toFixed(1)}%
                </p>
              </div>
              {isIncrease ? (
                <TrendingUp className="text-red-600" size={32} />
              ) : (
                <TrendingDown className="text-green-600" size={32} />
              )}
            </div>
          </div>
        </div>

        {/* カテゴリ別円グラフ */}
        {summary.category_breakdown.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">カテゴリ別支出</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={summary.category_breakdown}
                  dataKey="total"
                  nameKey="category_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.category_name}: ¥${entry.total.toLocaleString()}`}
                >
                  {summary.category_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 最近の出費 */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">最近の出費</h2>
          <ExpenseList
            expenses={recentExpenses}
            onEdit={handleEditExpense}
            onDelete={handleDeleteExpense}
            onViewReceipt={handleViewReceipt}
          />
        </div>
      </div>

      {/* レシート表示モーダル */}
      {selectedReceipt && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedReceipt(null)}
        >
          <div className="bg-white rounded-lg p-4 max-w-2xl max-h-[90vh] overflow-auto">
            <img
              src={receiptAPI.getReceiptImage(selectedReceipt)}
              alt="レシート"
              className="max-w-full h-auto"
            />
          </div>
        </div>
      )}

      {/* 編集モーダル */}
      {editingExpense && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setEditingExpense(null)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-4">出費を編集</h2>
            <form onSubmit={handleSaveEdit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  商品名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.product_name}
                  onChange={(e) => setEditForm({ ...editForm, product_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  金額 <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={editForm.amount || ''}
                  onChange={(e) => setEditForm({ ...editForm, amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  日付 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={editForm.expense_date}
                  onChange={(e) => setEditForm({ ...editForm, expense_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  店舗名（任意）
                </label>
                <input
                  type="text"
                  value={editForm.store_name}
                  onChange={(e) => setEditForm({ ...editForm, store_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  備考（任意）
                </label>
                <textarea
                  value={editForm.note}
                  onChange={(e) => setEditForm({ ...editForm, note: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  カテゴリ（任意）
                </label>
                <select
                  value={editForm.category_id || ''}
                  onChange={(e) => setEditForm({ ...editForm, category_id: e.target.value ? parseInt(e.target.value) : undefined })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">未分類</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setEditingExpense(null)}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  保存
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
}
