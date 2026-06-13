import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

export default function CreateGroup() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/groups/', { name, description });
      navigate(`/groups/${res.data.id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 500, margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title">Create Group</h1>
        <p className="page-subtitle">Start a new expense sharing group</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="group-name">Group Name</label>
            <input
              id="group-name"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Flat 42 Expenses"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="group-desc">Description (optional)</label>
            <textarea
              id="group-desc"
              className="form-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this group for?"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-lg w-full" disabled={loading}>
            {loading ? 'Creating...' : 'Create Group'}
          </button>
        </form>
      </div>
    </div>
  );
}
