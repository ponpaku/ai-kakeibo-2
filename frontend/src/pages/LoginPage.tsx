import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '@/services/api';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('🔐 Attempting login with username:', username);
      const response = await authAPI.login(username, password);
      console.log('📥 Login response received:', response);
      console.log('🎫 Access token:', response.access_token ? response.access_token.substring(0, 30) + '...' : 'MISSING!');
      console.log('👤 User data:', response.user);

      if (!response.access_token) {
        console.error('❌ ERROR: access_token is missing from response!');
        setError('ログインレスポンスにトークンがありません');
        return;
      }

      console.log('💾 Saving to localStorage...');
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // 保存を確認
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      console.log('✅ Saved token:', savedToken ? savedToken.substring(0, 30) + '...' : 'NOT SAVED!');
      console.log('✅ Saved user:', savedUser);

      if (!savedToken) {
        console.error('❌ ERROR: Failed to save token to localStorage!');
        setError('トークンの保存に失敗しました');
        return;
      }

      console.log('🚀 Redirecting to dashboard...');
      // ページ全体をリロードして、localStorageとaxiosインターセプターを確実に初期化
      window.location.href = '/';
    } catch (err: any) {
      console.error('❌ Login error:', err);
      console.error('❌ Error response:', err.response);
      setError(err.response?.data?.detail || 'ログインに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">
          AI家計簿
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              ユーザー名
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              パスワード
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'ログイン中...' : 'ログイン'}
          </button>
        </form>
      </div>
    </div>
  );
}
