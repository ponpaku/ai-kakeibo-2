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

    // デバッグ用：フォーム送信を確認
    const timestamp = new Date().toISOString();
    console.clear(); // コンソールをクリア
    console.log('='.repeat(60));
    console.log(`🔐 [${timestamp}] LOGIN ATTEMPT STARTED`);
    console.log(`   Username: ${username}`);
    console.log('='.repeat(60));

    try {
      const response = await authAPI.login(username, password);

      console.log('📥 LOGIN RESPONSE RECEIVED:');
      console.log('   Full response:', response);
      console.log('   Has access_token?', !!response.access_token);
      console.log('   Token (first 50 chars):', response.access_token?.substring(0, 50) + '...');
      console.log('   User:', response.user);

      if (!response.access_token) {
        console.error('❌ CRITICAL ERROR: access_token is MISSING from response!');
        alert('エラー: サーバーからトークンが返されませんでした');
        setError('ログインレスポンスにトークンがありません');
        setLoading(false);
        return;
      }

      console.log('💾 SAVING TO LOCALSTORAGE:');
      console.log('   Token length:', response.access_token.length);

      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // 即座に確認
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');

      console.log('✅ VERIFICATION:');
      console.log('   Token saved?', !!savedToken);
      console.log('   Token matches?', savedToken === response.access_token);
      console.log('   User saved?', !!savedUser);

      if (!savedToken) {
        console.error('❌ CRITICAL ERROR: Failed to save token to localStorage!');
        alert('エラー: localStorageへの保存に失敗しました');
        setError('トークンの保存に失敗しました');
        setLoading(false);
        return;
      }

      console.log('🚀 REDIRECTING to dashboard...');
      console.log('='.repeat(60));

      // 3秒後にリダイレクト（デバッグ用に時間を設ける）
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);

    } catch (err: any) {
      console.error('❌ LOGIN ERROR:');
      console.error('   Error:', err);
      console.error('   Response:', err.response);
      console.error('   Response data:', err.response?.data);
      console.error('   Status:', err.response?.status);

      alert(`ログインエラー: ${err.response?.data?.detail || err.message}`);
      setError(err.response?.data?.detail || 'ログインに失敗しました');
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
