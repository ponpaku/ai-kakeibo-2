import { format } from 'date-fns';
import { Edit, Trash2, Image as ImageIcon } from 'lucide-react';
import type { Expense } from '@/types';

interface ExpenseListProps {
  expenses: Expense[];
  onEdit: (expense: Expense) => void;
  onDelete: (expenseId: number) => void;
  onViewReceipt: (receiptId: number) => void;
}

export default function ExpenseList({ expenses, onEdit, onDelete, onViewReceipt }: ExpenseListProps) {
  const getStatusBadge = (status: string) => {
    const statusStyles = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    const statusLabels = {
      pending: '待機中',
      processing: '処理中',
      completed: '完了',
      failed: '失敗',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status as keyof typeof statusStyles]}`}>
        {statusLabels[status as keyof typeof statusLabels]}
      </span>
    );
  };

  return (
    <div className="bg-white shadow-md rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                日付
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                タイトル
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                カテゴリ
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                金額
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状態
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {expenses.map((expense) => {
              // すべてのユニークなカテゴリ名を取得
              const categories = expense.items && expense.items.length > 0
                ? [...new Set(expense.items.map(item => item.category_name).filter(Boolean))]
                : [];

              const categoryDisplay = categories.length > 0
                ? categories.join(', ')
                : '未分類';

              return (
                <tr key={expense.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(expense.occurred_at), 'yyyy/MM/dd')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>{expense.title || expense.merchant_name || '-'}</div>
                    {expense.items && expense.items.length > 1 && (
                      <div className="text-xs text-gray-500">他{expense.items.length - 1}件</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {categoryDisplay}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                    ¥{expense.total_amount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {getStatusBadge(expense.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      {expense.receipt && (
                        <button
                          onClick={() => onViewReceipt(expense.receipt!.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="レシートを表示"
                        >
                          <ImageIcon size={18} />
                        </button>
                      )}
                      <button
                        onClick={() => onEdit(expense)}
                        className="text-primary-600 hover:text-primary-900"
                        title="編集"
                      >
                        <Edit size={18} />
                      </button>
                      <button
                        onClick={() => {
                          if (window.confirm('この出費を削除しますか？')) {
                            onDelete(expense.id);
                          }
                        }}
                        className="text-red-600 hover:text-red-900"
                        title="削除"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
