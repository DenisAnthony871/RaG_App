import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';

export default function StatsPanel({ apiKey, isOpen }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.stats(apiKey);
      if (isMounted.current) setStats(data);
    } catch (err) {
      if (isMounted.current) {
        console.error('Failed to load stats:', err);
        setError('Failed to load stats');
        setStats(null);
      }
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, [apiKey]);

  // Fetch on mount
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return (
    <aside className={`stats-panel ${isOpen ? 'open' : ''}`}>
      <div className="stats-header">
        <h2>📊 System Stats</h2>
        <button
          id="stats-refresh-btn"
          className={`stats-refresh-btn${loading ? ' spinning' : ''}`}
          onClick={fetchStats}
          disabled={loading}
          title="Refresh stats"
        >
          ↻
        </button>
      </div>

      <div className="stats-body">
        {loading && (
          <div className="stats-loading">
            <div className="spinner"></div>
            <span>Loading stats…</span>
          </div>
        )}

        {error && !loading && (
          <div className="stats-error">{error}</div>
        )}

        {stats && !loading && (
          <>
            <div className="stats-card">
              <div className="stats-card-label">Total Vectors</div>
              <div className="stats-card-value">
                {stats.total_vectors?.toLocaleString() ?? '—'}
              </div>
            </div>

            <div className="stats-card">
              <div className="stats-card-label">Collection</div>
              <div className="stats-card-value small">
                {stats.collection || '—'}
              </div>
            </div>

            <div className="stats-card">
              <div className="stats-card-label">Database Path</div>
              <div className="stats-card-value small">
                {stats.db_path || '—'}
              </div>
            </div>
          </>
        )}

        {!loading && (
          <div className="stats-card">
            <div className="stats-card-label">Status</div>
            <div className="stats-card-value small">
              <span className={`status-dot ${error ? 'offline' : 'online'}`} style={error ? { background: '#ef4444' } : {}}></span>
              {error ? 'Disconnected' : 'Connected'}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
