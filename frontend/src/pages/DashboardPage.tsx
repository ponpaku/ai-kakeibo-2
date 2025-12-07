import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import Layout from '@/components/common/Layout';
import Loading from '@/components/common/Loading';
import ExpenseList from '@/components/Dashboard/ExpenseList';
import { dashboardAPI, expenseAPI, receiptAPI, categoryAPI } from '@/services/api';
import type { DashboardSummary, Expense, Category, ExpenseItem } from '@/types';
import { TrendingUp, TrendingDown, DollarSign, ShoppingBag } from 'lucide-react';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<number | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [editForm, setEditForm] = useState({
    title: '',
    total_amount: 0,
    occurred_at: '',
    merchant_name: '',
    note: '',
    payment_method: '',
  });
  const [editingItems, setEditingItems] = useState<ExpenseItem[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryData, expensesData, categoriesData] = await Promise.all([
        dashboardAPI.getSummary(),
        dashboardAPI.getRecentExpenses(10),
        categoryAPI.listCategories(),
      ]);
      setSummary(summaryData);
      setRecentExpenses(expensesData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditExpense = (expense: Expense) => {
    setEditingExpense(expense);
    setEditForm({
      title: expense.title || '',
      total_amount: expense.total_amount,
      occurred_at: expense.occurred_at.split('T')[0],
      merchant_name: expense.merchant_name || '',
      note: expense.note || '',
      payment_method: expense.payment_method || '',
    });
    // アイテムのコピーを作成して編集用に設定
    setEditingItems(expense.items ? [...expense.items] : []);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingExpense) return;

    try {
      // 出費ヘッダーを更新
      await expenseAPI.updateExpense(editingExpense.id, editForm);

      // 各アイテムを更新（変更があった場合のみ）
      const updatePromises = editingItems.map(async (item) => {
        const originalItem = editingExpense.items?.find(i => i.id === item.id);
        if (originalItem && (
          originalItem.category_id !== item.category_id ||
          originalItem.product_name !== item.product_name ||
          originalItem.line_total !== item.line_total
        )) {
          return expenseAPI.updateExpenseItem(editingExpense.id, item.id, {
            product_name: item.product_name,
            line_total: item.line_total,
            category_id: item.category_id,
          });
        }
      });

      await Promise.all(updatePromises);
      setEditingExpense(null);
      setEditingItems([]);
      loadData();
    } catch (error) {
      console.error('更新に失敗しました:', error);
      alert('更新に失敗しました');
    }
  };

  const handleItemChange = (itemId: number, field: keyof ExpenseItem, value: any) => {
    setEditingItems(items =>
      items.map(item =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    );
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
            className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-900 mb-4">出費を編集</h2>
            <form onSubmit={handleSaveEdit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  タイトル <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  合計金額 <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={editForm.total_amount || ''}
                  onChange={(e) => setEditForm({ ...editForm, total_amount: parseInt(e.target.value) || 0 })}
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
                  value={editForm.occurred_at}
                  onChange={(e) => setEditForm({ ...editForm, occurred_at: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  店舗名/加盟店名（任意）
                </label>
                <input
                  type="text"
                  value={editForm.merchant_name}
                  onChange={(e) => setEditForm({ ...editForm, merchant_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  支払い方法（任意）
                </label>
                <select
                  value={editForm.payment_method}
                  onChange={(e) => setEditForm({ ...editForm, payment_method: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">未選択</option>
                  <option value="cash">現金</option>
                  <option value="credit">クレジットカード</option>
                  <option value="debit">デビットカード</option>
                  <option value="e-money">電子マネー</option>
                  <option value="qr">QRコード決済</option>
                </select>
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

              {/* アイテム一覧 */}
              {editingItems.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    商品明細
                  </label>
                  <div className="border border-gray-300 rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">商品名</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">金額</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">カテゴリ</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {editingItems.map((item) => (
                          <tr key={item.id}>
                            <td className="px-4 py-2">
                              <input
                                type="text"
                                value={item.product_name}
                                onChange={(e) => handleItemChange(item.id, 'product_name', e.target.value)}
                                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                              />
                            </td>
                            <td className="px-4 py-2">
                              <input
                                type="number"
                                value={item.line_total}
                                onChange={(e) => handleItemChange(item.id, 'line_total', parseInt(e.target.value) || 0)}
                                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                              />
                            </td>
                            <td className="px-4 py-2">
                              <select
                                value={item.category_id || ''}
                                onChange={(e) => handleItemChange(item.id, 'category_id', e.target.value ? parseInt(e.target.value) : null)}
                                className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                              >
                                <option value="">未分類</option>
                                {categories.map((category) => (
                                  <option key={category.id} value={category.id}>
                                    {category.name}
                                  </option>
                                ))}
                              </select>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setEditingExpense(null);
                    setEditingItems([]);
                  }}
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
