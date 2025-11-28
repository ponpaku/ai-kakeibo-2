import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '@/components/common/Layout';
import Calculator from '@/components/Input/Calculator';
import { receiptAPI, expenseAPI, categoryAPI } from '@/services/api';
import type { Category } from '@/types';
import { Camera, FileText, Upload } from 'lucide-react';
import { useEffect } from 'react';

export default function InputPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'choice' | 'receipt' | 'manual'>('choice');
  const [categories, setCategories] = useState<Category[]>([]);

  // レシート入力用
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 手入力用
  const [manualForm, setManualForm] = useState({
    amount: 0,
    store_name: '',
    description: '',
    category_id: undefined as number | undefined,
    expense_date: new Date().toISOString().split('T')[0],
  });
  const [showCalculator, setShowCalculator] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await categoryAPI.listCategories();
      setCategories(data);
    } catch (error) {
      console.error('カテゴリの読み込みに失敗しました:', error);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleUploadReceipt = async (autoProcess: boolean) => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      await receiptAPI.uploadReceipt(selectedFile, autoProcess);
      alert(autoProcess ? 'レシートをアップロードし、処理を開始しました' : 'レシートをアップロードしました');
      navigate('/');
    } catch (error) {
      console.error('アップロードに失敗しました:', error);
      alert('アップロードに失敗しました');
    } finally {
      setUploading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await expenseAPI.createManualExpense({
        ...manualForm,
        expense_date: new Date(manualForm.expense_date).toISOString(),
      });
      alert('出費を記録しました');
      navigate('/');
    } catch (error) {
      console.error('記録に失敗しました:', error);
      alert('記録に失敗しました');
    }
  };

  if (mode === 'choice') {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">出費を記録</h1>
          <p className="text-gray-600 mb-8">どの方法で記録しますか？</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button
              onClick={() => setMode('receipt')}
              className="bg-white p-8 rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-primary-500"
            >
              <Camera className="mx-auto mb-4 text-primary-600" size={48} />
              <h2 className="text-xl font-bold text-gray-900 mb-2">レシート撮影</h2>
              <p className="text-gray-600">写真を撮るだけで自動入力</p>
            </button>

            <button
              onClick={() => setMode('manual')}
              className="bg-white p-8 rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-primary-500"
            >
              <FileText className="mx-auto mb-4 text-primary-600" size={48} />
              <h2 className="text-xl font-bold text-gray-900 mb-2">手入力</h2>
              <p className="text-gray-600">金額と内容を入力</p>
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  if (mode === 'receipt') {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => setMode('choice')}
            className="mb-6 text-primary-600 hover:text-primary-700"
          >
            ← 戻る
          </button>

          <h1 className="text-2xl font-bold text-gray-900 mb-6">レシート撮影</h1>

          <div className="bg-white p-6 rounded-lg shadow-md">
            {!previewUrl ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-primary-500 transition-colors"
              >
                <Upload className="mx-auto mb-4 text-gray-400" size={48} />
                <p className="text-gray-600 mb-2">クリックしてレシート画像を選択</p>
                <p className="text-sm text-gray-500">JPG, PNG, WEBP</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            ) : (
              <div>
                <img
                  src={previewUrl}
                  alt="レシートプレビュー"
                  className="max-w-full h-auto mx-auto mb-6 rounded-lg"
                />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => {
                      setPreviewUrl(null);
                      setSelectedFile(null);
                    }}
                    className="px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    撮り直す
                  </button>
                  <button
                    onClick={() => handleUploadReceipt(false)}
                    disabled={uploading}
                    className="px-4 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
                  >
                    {uploading ? '処理中...' : 'OCR実行'}
                  </button>
                  <button
                    onClick={() => handleUploadReceipt(true)}
                    disabled={uploading}
                    className="px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
                  >
                    {uploading ? '処理中...' : 'あとは任せる'}
                  </button>
                </div>
                <p className="text-sm text-gray-600 mt-4 text-center">
                  「OCR実行」: 結果を確認してから送信<br />
                  「あとは任せる」: 自動でOCRとAI分類を実行
                </p>
              </div>
            )}
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => setMode('choice')}
          className="mb-6 text-primary-600 hover:text-primary-700"
        >
          ← 戻る
        </button>

        <h1 className="text-2xl font-bold text-gray-900 mb-6">手入力</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 入力フォーム */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  金額 <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={manualForm.amount || ''}
                    onChange={(e) => setManualForm({ ...manualForm, amount: parseFloat(e.target.value) || 0 })}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowCalculator(!showCalculator)}
                    className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                  >
                    電卓
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  日付 <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={manualForm.expense_date}
                  onChange={(e) => setManualForm({ ...manualForm, expense_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  店舗名
                </label>
                <input
                  type="text"
                  value={manualForm.store_name}
                  onChange={(e) => setManualForm({ ...manualForm, store_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="例: スーパーマーケット"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  説明・メモ
                </label>
                <textarea
                  value={manualForm.description}
                  onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                  placeholder="例: 食材購入"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  カテゴリ（任意）
                </label>
                <select
                  value={manualForm.category_id || ''}
                  onChange={(e) => setManualForm({ ...manualForm, category_id: e.target.value ? parseInt(e.target.value) : undefined })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">AIに分類させる</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="w-full bg-primary-600 text-white py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
              >
                記録する
              </button>
            </form>
          </div>

          {/* 電卓 */}
          {showCalculator && (
            <div>
              <Calculator
                onCalculate={(value) => {
                  setManualForm({ ...manualForm, amount: value });
                  setShowCalculator(false);
                }}
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
