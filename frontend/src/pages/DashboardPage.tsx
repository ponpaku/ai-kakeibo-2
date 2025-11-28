import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import Layout from '@/components/common/Layout';
import Loading from '@/components/common/Loading';
import ExpenseList from '@/components/Dashboard/ExpenseList';
import { dashboardAPI, expenseAPI, receiptAPI } from '@/services/api';
import type { DashboardSummary, Expense } from '@/types';
import { TrendingUp, TrendingDown, DollarSign, ShoppingBag } from 'lucide-react';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<number | null>(null);

  useEffect(() => {
    loadData();
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

  const handleEditExpense = (expense: Expense) => {
    // 編集機能は簡略化のため省略（実装する場合はモーダルを追加）
    console.log('Edit expense:', expense);
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
    </Layout>
  );
}
