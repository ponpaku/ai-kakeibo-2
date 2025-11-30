import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '@/components/common/Layout';
import { expenseAPI, categoryAPI } from '@/services/api';
import type { Expense, Category } from '@/types';

export default function ExpenseEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [expense, setExpense] = useState<Expense | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    product_name: '',
    amount: 0,
    store_name: '',
    note: '',
    category_id: undefined as number | undefined,
    expense_date: '',
  });

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);

      const [expenseData, categoriesData] = await Promise.all([
        expenseAPI.getExpense(Number(id)),
        categoryAPI.listCategories(),
      ]);

      setExpense(expenseData);
      setCategories(categoriesData);

      setFormData({
        product_name: expenseData.product_name || '',
        amount: expenseData.amount || 0,
        store_name: expenseData.store_name || '',
        note: expenseData.note || '',
        category_id: expenseData.category_id,
        expense_date: expenseData.expense_date
          ? new Date(expenseData.expense_date).toISOString().split('T')[0]
          : new Date().toISOString().split('T')[0],
      });
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
      alert('データの読み込みに失敗しました');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_name.trim()) {
      alert('商品名を入力してください');
      return;
    }

    setSaving(true);

    try {
      await expenseAPI.updateExpense(Number(id), {
        ...formData,
        expense_date: new Date(formData.expense_date).toISOString(),
      });

      alert('出費を更新しました');
      navigate('/');
    } catch (error) {
      console.error('更新に失敗しました:', error);
      alert('更新に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!expense) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <p className="text-center text-gray-600 py-12">出費が見つかりませんでした</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/')}
          className="mb-6 text-primary-600 hover:text-primary-700"
        >
          ← ダッシュボードに戻る
        </button>

        <h1 className="text-2xl font-bold text-gray-900 mb-6">出費を編集</h1>

        {/* OCR結果表示 */}
        {expense.ocr_raw_text && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-2">OCR結果</h2>
            <pre className="text-xs text-gray-600 whitespace-pre-wrap max-h-40 overflow-y-auto">
              {expense.ocr_raw_text}
            </pre>
          </div>
        )}

        <div className="bg-white p-6 rounded-lg shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                商品名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.product_name}
                onChange={(e) =>
                  setFormData({ ...formData, product_name: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例: キュキュット、洗剤、食材など"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                金額 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.amount || ''}
                onChange={(e) =>
                  setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })
                }
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
                value={formData.expense_date}
                onChange={(e) =>
                  setFormData({ ...formData, expense_date: e.target.value })
                }
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
                value={formData.store_name}
                onChange={(e) =>
                  setFormData({ ...formData, store_name: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例: スーパーマーケット"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                備考（任意）
              </label>
              <textarea
                value={formData.note}
                onChange={(e) =>
                  setFormData({ ...formData, note: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
                placeholder="例: セール品、まとめ買いなど"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                カテゴリ（任意）
              </label>
              <select
                value={formData.category_id || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    category_id: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">AIに分類させる</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 bg-primary-600 text-white py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {saving ? '保存中...' : '保存する'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                キャンセル
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
}
