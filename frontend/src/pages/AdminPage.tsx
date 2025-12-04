import React, { useState, useEffect } from 'react';
import Layout from '@/components/common/Layout';
import { userAPI, categoryAPI, aiSettingsAPI, categoryRuleAPI } from '@/services/api';
import type { User, Category, AISettings, CategoryRule } from '@/types';
import { Plus, Edit, Trash2, Settings } from 'lucide-react';

export default function AdminPage() {
  const [tab, setTab] = useState<'categories' | 'users' | 'ai-settings' | 'category-rules'>('categories');
  const getInitialRuleForm = (defaultCategoryId?: number): Partial<CategoryRule> => ({
    name: '',
    pattern: '',
    match_type: 'contains' as CategoryRule['match_type'],
    category_id: defaultCategoryId,
    confidence: 0.8,
    priority: 100,
    is_active: true,
  });
  const [users, setUsers] = useState<User[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryRules, setCategoryRules] = useState<CategoryRule[]>([]);
  const [aiSettings, setAiSettings] = useState<AISettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [ruleSaving, setRuleSaving] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [editingRule, setEditingRule] = useState<CategoryRule | null>(null);
  const [ruleForm, setRuleForm] = useState<Partial<CategoryRule>>(getInitialRuleForm());
  const [testText, setTestText] = useState('');
  const [testResult, setTestResult] = useState('');

  useEffect(() => {
    loadData();
  }, [tab]);

  const loadData = async () => {
    try {
      if (tab === 'users') {
        const data = await userAPI.listUsers();
        setUsers(data);
      } else if (tab === 'categories') {
        const data = await categoryAPI.listCategories(false);
        setCategories(data);
      } else if (tab === 'ai-settings') {
        const data = await aiSettingsAPI.getSettings();
        setAiSettings(data);
      } else if (tab === 'category-rules') {
        const [categoryData, ruleData] = await Promise.all([
          categoryAPI.listCategories(false),
          categoryRuleAPI.listRules(),
        ]);
        setCategories(categoryData);
        setCategoryRules(ruleData);
        if (!editingRule) {
          setRuleForm(getInitialRuleForm(categoryData[0]?.id));
        }
      }
    } catch (error) {
      console.error('データの読み込みに失敗しました:', error);
    }
  };

  const handleDeleteCategory = async (categoryId: number) => {
    if (!window.confirm('このカテゴリを削除しますか？')) return;

    try {
      await categoryAPI.deleteCategory(categoryId);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || '削除に失敗しました');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm('このユーザーを削除しますか？')) return;

    try {
      await userAPI.deleteUser(userId);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || '削除に失敗しました');
    }
  };

  const handleEditRule = (rule: CategoryRule) => {
    setEditingRule(rule);
    setRuleForm(rule);
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!window.confirm('このルールを削除しますか？')) return;
    try {
      await categoryRuleAPI.deleteRule(ruleId);
      setEditingRule(null);
      setRuleForm(getInitialRuleForm(categories[0]?.id));
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || '削除に失敗しました');
    }
  };

  const handleSubmitRule = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!ruleForm.category_id) {
      alert('カテゴリを選択してください');
      return;
    }

    setRuleSaving(true);
    try {
      const { id, ...payload } = ruleForm;
      if (editingRule) {
        const updated = await categoryRuleAPI.updateRule(editingRule.id, payload);
        setEditingRule(updated);
      } else {
        await categoryRuleAPI.createRule(payload as Omit<CategoryRule, 'id'>);
      }
      setRuleForm(getInitialRuleForm(categories[0]?.id));
      setEditingRule(null);
      await loadData();
      alert('ルールを保存しました');
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存に失敗しました');
    } finally {
      setRuleSaving(false);
    }
  };

  const handleTestRule = async () => {
    if (!testText.trim()) return;
    setTestResult('判定中...');
    try {
      const result = await categoryRuleAPI.testRule(testText.trim());
      if (result.matched && result.rule) {
        setTestResult(
          `ヒット: ${result.rule.name || '名称未設定'} → ${result.category_name || 'カテゴリ未設定'}`,
        );
      } else {
        setTestResult('ヒットするルールはありませんでした');
      }
    } catch (error: any) {
      setTestResult(error.response?.data?.detail || 'テストに失敗しました');
    }
  };

  const handleSaveAISettings = async () => {
    if (!aiSettings) return;

    setSaving(true);
    try {
      const updated = await aiSettingsAPI.updateSettings({
        ocr_model: aiSettings.ocr_model,
        ocr_enabled: aiSettings.ocr_enabled,
        classification_model: aiSettings.classification_model,
        classification_enabled: aiSettings.classification_enabled,
        sandbox_mode: aiSettings.sandbox_mode,
        skip_git_repo_check: aiSettings.skip_git_repo_check,
        ocr_system_prompt: aiSettings.ocr_system_prompt,
        classification_system_prompt: aiSettings.classification_system_prompt,
      });
      setAiSettings(updated);
      alert('AI設定を保存しました');
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">管理画面</h1>

        {/* タブ */}
        <div className="flex gap-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setTab('categories')}
            className={`px-4 py-2 font-medium transition-colors ${
              tab === 'categories'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            カテゴリ管理
          </button>
          <button
            onClick={() => setTab('users')}
            className={`px-4 py-2 font-medium transition-colors ${
              tab === 'users'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            ユーザー管理
          </button>
          <button
            onClick={() => setTab('ai-settings')}
            className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
              tab === 'ai-settings'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Settings size={18} />
            AI設定
          </button>
          <button
            onClick={() => setTab('category-rules')}
            className={`px-4 py-2 font-medium transition-colors ${
              tab === 'category-rules'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            分類ルール
          </button>
        </div>

        {/* カテゴリ管理 */}
        {tab === 'categories' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">カテゴリ一覧</h2>
              <button
                onClick={() => {
                  setEditingItem(null);
                  setShowModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Plus size={20} />
                新規作成
              </button>
            </div>

            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">色</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">名前</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">説明</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状態</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {categories.map((category) => (
                    <tr key={category.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div
                          className="w-8 h-8 rounded-full"
                          style={{ backgroundColor: category.color }}
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {category.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {category.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          category.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {category.is_active ? '有効' : '無効'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setEditingItem(category);
                              setShowModal(true);
                            }}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            <Edit size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteCategory(category.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ユーザー管理 */}
        {tab === 'users' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">ユーザー一覧</h2>
              <button
                onClick={() => {
                  setEditingItem(null);
                  setShowModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Plus size={20} />
                新規作成
              </button>
            </div>

            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ユーザー名</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">メール</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">権限</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状態</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {user.username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_admin
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {user.is_admin ? '管理者' : '一般'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {user.is_active ? '有効' : '無効'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setEditingItem(user);
                              setShowModal(true);
                            }}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            <Edit size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 分類ルール管理 */}
        {tab === 'category-rules' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                {editingRule ? 'ルール編集' : '新規ルール作成'}
              </h2>
              <form className="space-y-4" onSubmit={handleSubmitRule}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">名称（任意）</label>
                    <input
                      type="text"
                      value={ruleForm.name || ''}
                      onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="例: 米（食費）"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">一致タイプ</label>
                    <select
                      value={ruleForm.match_type || 'contains'}
                      onChange={(e) =>
                        setRuleForm({ ...ruleForm, match_type: e.target.value as CategoryRule['match_type'] })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="contains">部分一致（|区切り可）</option>
                      <option value="regex">正規表現</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">パターン</label>
                    <input
                      type="text"
                      value={ruleForm.pattern || ''}
                      onChange={(e) => setRuleForm({ ...ruleForm, pattern: e.target.value })}
                      required
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="例: 米|こめ|コメ"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">カテゴリ</label>
                    <select
                      value={ruleForm.category_id || ''}
                      onChange={(e) => setRuleForm({ ...ruleForm, category_id: Number(e.target.value) })}
                      required
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="" disabled>
                        選択してください
                      </option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">優先度（小さいほど先）</label>
                    <input
                      type="number"
                      value={ruleForm.priority ?? 100}
                      onChange={(e) => setRuleForm({ ...ruleForm, priority: Number(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">信頼度(0-1)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={ruleForm.confidence ?? 0.8}
                      onChange={(e) => setRuleForm({ ...ruleForm, confidence: Number(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    />
                  </div>
                  <div className="flex items-center gap-3 pt-6">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={ruleForm.is_active ?? true}
                        onChange={(e) => setRuleForm({ ...ruleForm, is_active: e.target.checked })}
                        className="w-5 h-5 text-primary-600"
                      />
                      <span className="font-medium">有効</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-3">
                  {editingRule && (
                    <button
                      type="button"
                      onClick={() => {
                        setEditingRule(null);
                        setRuleForm(getInitialRuleForm(categories[0]?.id));
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                    >
                      リセット
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={ruleSaving}
                    className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {ruleSaving ? '保存中...' : '保存'}
                  </button>
                </div>
              </form>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">ルール一覧</h3>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="テキストでテスト"
                    value={testText}
                    onChange={(e) => setTestText(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    type="button"
                    onClick={handleTestRule}
                    className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900"
                  >
                    テスト
                  </button>
                </div>
              </div>
              {testResult && <p className="text-sm text-gray-700">{testResult}</p>}

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">優先度</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状態</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">タイプ</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">パターン</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">カテゴリ</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">信頼度</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {categoryRules.map((rule) => {
                      const categoryName = categories.find((cat) => cat.id === rule.category_id)?.name || '-';
                      return (
                        <tr key={rule.id}>
                          <td className="px-4 py-3 text-sm text-gray-900">{rule.priority}</td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded-full ${
                                rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {rule.is_active ? '有効' : '無効'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">{rule.match_type}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{rule.pattern}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{categoryName}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{rule.confidence.toFixed(2)}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleEditRule(rule)}
                                className="text-primary-600 hover:text-primary-900"
                              >
                                <Edit size={18} />
                              </button>
                              <button
                                onClick={() => handleDeleteRule(rule.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {categoryRules.length === 0 && (
                      <tr>
                        <td className="px-4 py-3 text-sm text-gray-500" colSpan={7}>
                          ルールが登録されていません
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* AI設定 */}
        {tab === 'ai-settings' && aiSettings && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-6">AI設定（Codex Exec）</h2>

            <div className="bg-white p-6 rounded-lg shadow-md space-y-6">
              {/* OCR設定 */}
              <div className="border-b pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">OCR設定</h3>

                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={aiSettings.ocr_enabled}
                        onChange={(e) =>
                          setAiSettings({ ...aiSettings, ocr_enabled: e.target.checked })
                        }
                        className="w-5 h-5 text-primary-600"
                      />
                      <span className="font-medium">OCRを有効化</span>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      OCRモデル
                    </label>
                    <input
                      type="text"
                      value={aiSettings.ocr_model}
                      onChange={(e) =>
                        setAiSettings({ ...aiSettings, ocr_model: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="gpt-5.1-codex-mini"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      例: gpt-5.1-codex-mini, gpt-4, gpt-3.5-turbo など
                    </p>
                  </div>
                </div>
              </div>

              {/* 分類設定 */}
              <div className="border-b pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">分類設定</h3>

                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={aiSettings.classification_enabled}
                        onChange={(e) =>
                          setAiSettings({
                            ...aiSettings,
                            classification_enabled: e.target.checked,
                          })
                        }
                        className="w-5 h-5 text-primary-600"
                      />
                      <span className="font-medium">AI分類を有効化</span>
                    </label>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      分類モデル
                    </label>
                    <input
                      type="text"
                      value={aiSettings.classification_model}
                      onChange={(e) =>
                        setAiSettings({
                          ...aiSettings,
                          classification_model: e.target.value,
                        })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      placeholder="gpt-5.1-codex-mini"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      例: gpt-5.1-codex-mini, gpt-4, gpt-3.5-turbo など
                    </p>
                  </div>
                </div>
              </div>

              {/* Codex Exec共通設定 */}
              <div className="border-b pb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Codex Exec共通設定
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      サンドボックスモード
                    </label>
                    <select
                      value={aiSettings.sandbox_mode}
                      onChange={(e) =>
                        setAiSettings({ ...aiSettings, sandbox_mode: e.target.value })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="read-only">read-only（推奨）</option>
                      <option value="none">none</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      セキュリティのため read-only を推奨します
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={aiSettings.skip_git_repo_check}
                        onChange={(e) =>
                          setAiSettings({
                            ...aiSettings,
                            skip_git_repo_check: e.target.checked,
                          })
                        }
                        className="w-5 h-5 text-primary-600"
                      />
                      <span className="font-medium">Gitリポジトリチェックをスキップ</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* 保存ボタン */}
              <div className="flex justify-end">
                <button
                  onClick={handleSaveAISettings}
                  disabled={saving}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {saving ? '保存中...' : '設定を保存'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* モーダル（簡略化のため実装は省略） */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-bold mb-4">
              {editingItem ? '編集' : '新規作成'}
            </h3>
            <p className="text-gray-600 mb-4">モーダルの実装は簡略化しています</p>
            <button
              onClick={() => setShowModal(false)}
              className="w-full bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600"
            >
              閉じる
            </button>
          </div>
        </div>
      )}
    </Layout>
  );
}
