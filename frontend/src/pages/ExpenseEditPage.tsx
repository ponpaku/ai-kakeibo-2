import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '@/components/common/Layout';
import { expenseAPI, categoryAPI } from '@/services/api';
import type { Expense, Category } from '@/types';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useGlobalModal } from '@/contexts/ModalContext';

interface EditItemForm {
  id: number;
  product_name: string;
  quantity: number | null;
  unit_price: number | null;
  line_total: number;
  tax_rate: number | null;
  tax_included: boolean | null;
  tax_amount: number | null;
  category_id: number | null;
}

export default function ExpenseEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showError, showSuccess, showWarning } = useGlobalModal();

  const [expense, setExpense] = useState<Expense | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showItemsSection, setShowItemsSection] = useState(true);

  const [formData, setFormData] = useState({
    title: '',
    total_amount: 0,
    occurred_at: '',
    merchant_name: '',
    note: '',
    payment_method: '',
  });

  const [editItemsForm, setEditItemsForm] = useState<EditItemForm[]>([]);

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
        title: expenseData.title || '',
        total_amount: expenseData.total_amount || 0,
        occurred_at: expenseData.occurred_at
          ? expenseData.occurred_at.split('T')[0]
          : new Date().toISOString().split('T')[0],
        merchant_name: expenseData.merchant_name || '',
        note: expenseData.note || '',
        payment_method: expenseData.payment_method || '',
      });

      // items フォームを初期化
      if (expenseData.items && expenseData.items.length > 0) {
        setEditItemsForm(expenseData.items.map(item => ({
          id: item.id,
          product_name: item.product_name,
          quantity: item.quantity ?? null,
          unit_price: item.unit_price ?? null,
          line_total: item.line_total,
          tax_rate: item.tax_rate ?? null,
          tax_included: item.tax_included ?? null,
          tax_amount: item.tax_amount ?? null,
          category_id: item.category_id ?? null,
        })));
      } else {
        setEditItemsForm([]);
      }
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
      showError('データの読み込みに失敗しました');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleItemFormChange = (itemId: number, field: keyof EditItemForm, value: string | number | null) => {
    setEditItemsForm(prev => prev.map(item =>
      item.id === itemId ? { ...item, [field]: value } : item
    ));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      showWarning('タイトルを入力してください');
      return;
    }

    setSaving(true);

    try {
      // Expense本体の更新
      await expenseAPI.updateExpense(Number(id), {
        title: formData.title,
        total_amount: formData.total_amount,
        occurred_at: formData.occurred_at,
        merchant_name: formData.merchant_name,
        note: formData.note,
        payment_method: formData.payment_method,
      });

      // 各ExpenseItemの更新
      for (const itemForm of editItemsForm) {
        const originalItem = expense?.items?.find(i => i.id === itemForm.id);
        if (originalItem) {
          // 変更があったかチェック
          const hasChanges =
            originalItem.product_name !== itemForm.product_name ||
            originalItem.line_total !== itemForm.line_total ||
            (originalItem.category_id ?? null) !== itemForm.category_id;

          if (hasChanges) {
            await expenseAPI.updateExpenseItem(Number(id), itemForm.id, {
              product_name: itemForm.product_name,
              line_total: itemForm.line_total,
              tax_rate: itemForm.tax_rate,
              tax_included: itemForm.tax_included,
              tax_amount: itemForm.tax_amount,
              category_id: itemForm.category_id,
            });
          }
        }
      }

      showSuccess('出費を更新しました');
      navigate('/');
    } catch (error) {
      console.error('更新に失敗しました:', error);
      showError('更新に失敗しました');
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

        <div className="bg-white p-6 rounded-lg shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                タイトル <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例: セブン-イレブンでの購入"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                合計金額 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.total_amount || ''}
                onChange={(e) => setFormData({ ...formData, total_amount: parseInt(e.target.value) || 0 })}
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
                value={formData.occurred_at}
                onChange={(e) => setFormData({ ...formData, occurred_at: e.target.value })}
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
                value={formData.merchant_name}
                onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
                className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="例: セブン-イレブン"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                支払い方法（任意）
              </label>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
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
                value={formData.note}
                onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                className="w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
                placeholder="例: セール品、まとめ買いなど"
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

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
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
                              数量
                            </label>
                            <input
                              type="number"
                              step="0.001"
                              value={item.quantity ?? ''}
                              onChange={(e) => handleItemFormChange(item.id, 'quantity', e.target.value ? parseFloat(e.target.value) : null)}
                              className="w-full px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              金額 <span className={`text-xs ${item.tax_included ? 'text-green-600' : 'text-orange-600'}`}>({item.tax_included ? '税込' : '税抜'})</span>
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

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              税率
                            </label>
                            <select
                              value={item.tax_rate ?? ''}
                              onChange={(e) => handleItemFormChange(item.id, 'tax_rate', e.target.value ? parseFloat(e.target.value) : null)}
                              className="w-full px-3 py-1.5 bg-white text-gray-900 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                            >
                              <option value="">未設定</option>
                              <option value="8">8%（軽減税率）</option>
                              <option value="10">10%（標準税率）</option>
                            </select>
                          </div>

                          <div className="flex items-center">
                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={item.tax_included ?? true}
                                onChange={(e) => handleItemFormChange(item.id, 'tax_included', e.target.checked)}
                                className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                              />
                              <span className="text-xs text-gray-600">税込み価格</span>
                            </label>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-4 pt-4">
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
