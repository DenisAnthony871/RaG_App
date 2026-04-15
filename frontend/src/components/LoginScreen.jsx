import { useState } from 'react';
import { api } from '../api';

export default function LoginScreen({ onLogin }) {
  const [key, setKey] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!key.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // 1. Confirm server is up
      await api.health();
      // 2. Validate the key (401 if wrong)
      await api.stats(key.trim());
      // 3. Both succeed — log in
      if (typeof onLogin === 'function') {
        onLogin(key.trim());
      } else {
        setError('Configuration error: Login handler missing');
      }
    } catch (err) {
      const isAuthError = err.status === 401 || err.response?.status === 401 || (err.message && err.message.toLowerCase().includes('401')) || (err.message && err.message.toLowerCase().includes('unauthorized'));
      if (isAuthError) {
        setError('Invalid API key');
      } else {
        setError('Server unavailable');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-logo">J</div>
        <h1>Jio RAG Support</h1>
        <p>Enter your API key to continue</p>

        <div className="login-input-group">
          <label htmlFor="api-key-input">API Key</label>
          <input
            id="api-key-input"
            className="login-input"
            type="password"
            placeholder="Enter your API key…"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            disabled={loading}
            autoFocus
          />
        </div>

        <button
          id="login-submit"
          className="login-btn"
          type="submit"
          disabled={loading || !key.trim()}
        >
          {loading ? 'Connecting…' : 'Sign In'}
        </button>

        {error && <div className="login-error">{error}</div>}
      </form>
    </div>
  );
}
