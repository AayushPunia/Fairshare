import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = (name) => {
    setUsername(name.toLowerCase());
    setPassword(name.toLowerCase());
  };

  return (
    <div className="login-page">
      <div className="login-card animate-fadeIn">
        <div className="login-title">
          <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>💰</div>
          <h1 className="page-title" style={{ fontSize: 'var(--font-2xl)' }}>FairShare</h1>
        </div>
        <p className="login-subtitle">Split expenses fairly with your flatmates</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-username">Username</label>
            <input
              id="login-username"
              className="form-input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          {error && <p className="form-error" style={{ marginBottom: '16px' }}>{error}</p>}

          <button
            type="submit"
            className="btn btn-primary btn-lg w-full"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: 'var(--space-xl)', textAlign: 'center' }}>
          <p className="text-sm text-muted" style={{ marginBottom: '12px' }}>Quick login as:</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
            {['Aisha', 'Rohan', 'Priya', 'Meera', 'Dev', 'Sam'].map((name) => (
              <button
                key={name}
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => quickLogin(name)}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
