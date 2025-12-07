import { useState, useEffect, useCallback } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import Layout from '@/components/common/Layout';
import Loading from '@/components/common/Loading';
import ExpenseList from '@/components/Dashboard/ExpenseList';
import { dashboardAPI, expenseAPI, receiptAPI, categoryAPI } from '@/services/api';
import type { DashboardSummary, Expense, Category } from '@/types';
import { TrendingUp, TrendingDown, DollarSign, ShoppingBag, ChevronDown, ChevronUp, ChevronLeft, ChevronRight } from 'lucide-react';

interface EditItemForm {
  id: number;
  product_name: string;
  line_total: number;
  category_id: number | null;
}

export default function DashboardPage() {
  const [selectedMonth, setSelectedMonth] = useState(new Date());
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceiptUrl, setSelectedReceiptUrl] = useState<string | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showItemsSection, setShowItemsSection] = useState(true);
  const [editForm, setEditForm] = useState({
    title: '',
    total_amount: 0,
    occurred_at: '',
    merchant_name: '',
    note: '',
    payment_method: '',
  });
  const [editItemsForm, setEditItemsForm] = useState<EditItemForm[]>([]);

  // 月の開始日と終了日を計算
  const getMonthRange = useCallback((date: Date) => {
    const startDate = new Date(date.getFullYear(), date.getMonth(), 1);
    const endDate = new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59);
    return {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString()
    };
  }, []);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const { startDate, endDate } = getMonthRange(selectedMonth);
      const [summaryData, expensesData] = await Promise.all([
        dashboardAPI.getSummary(startDate, endDate),
        dashboardAPI.getRecentExpenses(10),
      ]);
      setSummary(summaryData);
      setRecentExpenses(expensesData);
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedMonth, getMonthRange]);

  useEffect(() => {
    loadData();
    loadCategories();
  }, [loadData]);

  // 処理中のexpenseが存在するかチェック
  const hasProcessingExpenses = recentExpenses.some(
    expense => expense.status === 'processing' || expense.status === 'pending'
  );

  // 処理中のexpenseがある場合、ポーリングでデータを再取得
  useEffect(() => {
    if (!hasProcessingExpenses) return;

    const pollInterval = setInterval(() => {
      loadData();
    }, 3000); // 3秒間隔

    return () => clearInterval(pollInterval);
  }, [hasProcessingExpenses, loadData]);

  // 月を切り替える関数
  const handlePreviousMonth = () => {
    setSelectedMonth(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setSelectedMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  // 選択中の月を表示用にフォーマット
  const formatMonth = (date: Date) => {
    return `${date.getFullYear()}年${date.getMonth() + 1}月`;
  };

  // 今月かどうかを判定
  const isCurrentMonth = (date: Date) => {
    const now = new Date();
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth();
  };

  const loadCategories = async () => {
    try {
      const categoriesData = await categoryAPI.listCategories();
      setCategories(categoriesData);
    } catch (error) {
      console.error('カテゴリの読み込みに失敗しました:', error);
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
    // items フォームを初期化
    if (expense.items && expense.items.length > 0) {
      setEditItemsForm(expense.items.map(item => ({
        id: item.id,
        product_name: item.product_name,
        line_total: item.line_total,
        category_id: item.category_id ?? null,
      })));
    } else {
      setEditItemsForm([]);
    }
    setShowItemsSection(true);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingExpense) return;

    try {
      // Expense本体の更新
      await expenseAPI.updateExpense(editingExpense.id, editForm);

      // 各ExpenseItemの更新
      for (const itemForm of editItemsForm) {
        const originalItem = editingExpense.items?.find(i => i.id === itemForm.id);
        if (originalItem) {
          // 変更があったかチェック
          const hasChanges =
            originalItem.product_name !== itemForm.product_name ||
            originalItem.line_total !== itemForm.line_total ||
            (originalItem.category_id ?? null) !== itemForm.category_id;

          if (hasChanges) {
            await expenseAPI.updateExpenseItem(editingExpense.id, itemForm.id, {
              product_name: itemForm.product_name,
              line_total: itemForm.line_total,
              category_id: itemForm.category_id,
            });
          }
        }
      }

      setEditingExpense(null);
      loadData();
    } catch (error) {
      console.error('更新に失敗しました:', error);
      alert('更新に失敗しました');
    }
  };

  const handleItemFormChange = (itemId: number, field: keyof EditItemForm, value: string | number | null) => {
    setEditItemsForm(prev => prev.map(item =>
      item.id === itemId ? { ...item, [field]: value } : item
    ));
  };

  const handleDeleteExpense = async (expenseId: number) => {
    try {
      await expenseAPI.deleteExpense(expenseId);
      loadData();
    } catch (error) {
      console.error('削除に失敗しました:', error);
    }
  };

  const handleViewReceipt = async (receiptId: number) => {
    try {
      const url = await receiptAPI.getReceiptImageUrl(receiptId);
      setSelectedReceiptUrl(url);
    } catch (error) {
      console.error('レシート画像の取得に失敗しました:', error);
    }
  };

  const handleCloseReceipt = () => {
    if (selectedReceiptUrl) {
      URL.revokeObjectURL(selectedReceiptUrl);
    }
    setSelectedReceiptUrl(null);
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
        {/* 月別サマリーセクション */}
        <section className="bg-gray-50 p-6 rounded-xl">
          {/* 月切り替えヘッダー */}
          <div className="flex items-center justify-center gap-4 mb-6">
            <button
              onClick={handlePreviousMonth}
              className="p-2 rounded-full hover:bg-gray-200 transition-colors"
              aria-label="前月"
            >
              <ChevronLeft className="text-gray-600" size={24} />
            </button>
            <h2 className="text-2xl font-bold text-gray-900">
              {formatMonth(selectedMonth)}の概要
            </h2>
            <button
              onClick={handleNextMonth}
              disabled={isCurrentMonth(selectedMonth)}
              className={`p-2 rounded-full transition-colors ${isCurrentMonth(selectedMonth)
                ? 'text-gray-300 cursor-not-allowed'
                : 'hover:bg-gray-200 text-gray-600'
                }`}
              aria-label="次月"
            >
              <ChevronRight size={24} />
            </button>
          </div>

          {/* サマリーカード */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">支出合計</p>
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
              <h3 className="text-lg font-bold text-gray-900 mb-4">カテゴリ別支出</h3>
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
        </section>

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
      {selectedReceiptUrl && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseReceipt}
        >
          <div className="bg-white rounded-lg p-4 max-w-2xl max-h-[90vh] overflow-auto">
            <img
              src={selectedReceiptUrl}
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
                  タイトル <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  支払い方法（任意）
                </label>
                <select
                  value={editForm.payment_method}
                  onChange={(e) => setEditForm({ ...editForm, payment_method: e.target.value })}
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              {/* 商品明細セクション */}
              {editItemsForm.length > 0 && (
                <div className="border-t pt-4">
                  <button
                    type="button"
                    onClick={() => setShowItemsSection(!showItemsSection)}
                    className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3 hover:text-gray-900"
                  >
                    {showItemsSection ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    商品明細 ({editItemsForm.length}件)
                  </button>

                  {showItemsSection && (
                    <div className="space-y-3">
                      {editItemsForm.map((item, index) => (
                        <div key={item.id} className="bg-gray-50 rounded-lg p-4 space-y-3">
                          <div className="text-xs text-gray-500 font-medium">商品 {index + 1}</div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">
                                商品名
                              </label>
                              <input
                                type="text"
                                value={item.product_name}
                                onChange={(e) => handleItemFormChange(item.id, 'product_name', e.target.value)}
                                className="w-full px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                              />
                            </div>

                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">
                                金額
                              </label>
                              <input
                                type="number"
                                value={item.line_total || ''}
                                onChange={(e) => handleItemFormChange(item.id, 'line_total', parseInt(e.target.value) || 0)}
                                className="w-full px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              カテゴリ
                            </label>
                            <select
                              value={item.category_id ?? ''}
                              onChange={(e) => handleItemFormChange(item.id, 'category_id', e.target.value ? parseInt(e.target.value) : null)}
                              className="w-full px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                            >
                              <option value="">未分類</option>
                              {categories.map(cat => (
                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

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
