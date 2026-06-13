import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { HiOutlineBanknotes, HiOutlineUserGroup, HiOutlinePlusCircle } from 'react-icons/hi2';

export default function Dashboard() {
  const { user } = useAuth();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/groups/')
      .then((res) => setGroups(res.data.results || res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Welcome back, {user?.display_name} 👋</h1>
        <p className="page-subtitle">Manage your shared expenses</p>
      </div>

      <div className="stat-grid">
        <div className="stat-card glass-card">
          <div className="stat-value" style={{ color: 'var(--accent-secondary)' }}>
            <HiOutlineUserGroup />
          </div>
          <div className="stat-label">Groups</div>
          <div className="stat-value">{groups.length}</div>
        </div>
      </div>

      <div className="card-header" style={{ marginBottom: 'var(--space-md)' }}>
        <h2 className="card-title">Your Groups</h2>
        <Link to="/groups/new" className="btn btn-primary btn-sm">
          <HiOutlinePlusCircle /> New Group
        </Link>
      </div>

      {groups.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏠</div>
          <p className="empty-state-title">No groups yet</p>
          <p>Create a group to start tracking shared expenses</p>
          <Link to="/groups/new" className="btn btn-primary mt-md">Create Group</Link>
        </div>
      ) : (
        <div className="card-grid">
          {groups.map((group, i) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              style={{ textDecoration: 'none' }}
              className={`animate-fadeIn stagger-${i + 1}`}
            >
              <div className="glass-card" style={{ cursor: 'pointer' }}>
                <div className="flex items-center gap-md" style={{ marginBottom: '12px' }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: 'var(--radius-md)',
                    background: 'var(--accent-gradient)', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem'
                  }}>
                    🏠
                  </div>
                  <div>
                    <h3 style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{group.name}</h3>
                    <p className="text-sm text-muted">{group.member_count} members</p>
                  </div>
                </div>
                {group.description && (
                  <p className="text-sm text-secondary">{group.description}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
