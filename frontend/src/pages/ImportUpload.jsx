import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { HiOutlineDocumentArrowUp, HiOutlineExclamationTriangle } from 'react-icons/hi2';

export default function ImportUpload() {
  const [groups, setGroups] = useState([]);
  const [groupId, setGroupId] = useState('');
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef();
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/groups/').then(res => setGroups(res.data.results || res.data));
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.name.endsWith('.csv')) {
      setFile(dropped);
    }
  };

  const handleUpload = async () => {
    if (!file || !groupId) return;
    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('group_id', groupId);

    try {
      const res = await api.post('/import/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      navigate(`/import/${res.data.id}/review`);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 600, margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title">Import CSV</h1>
        <p className="page-subtitle">Upload your expenses spreadsheet for automatic anomaly detection</p>
      </div>

      <div className="card">
        <div className="form-group">
          <label className="form-label">Select Group</label>
          <select className="form-select" value={groupId} onChange={e => setGroupId(e.target.value)} required>
            <option value="">Choose a group...</option>
            {groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}
          </select>
        </div>

        <div
          className={`file-upload-zone ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
        >
          <input
            type="file"
            ref={fileRef}
            accept=".csv"
            style={{ display: 'none' }}
            onChange={(e) => setFile(e.target.files[0])}
          />
          <div className="file-upload-icon">
            <HiOutlineDocumentArrowUp />
          </div>
          {file ? (
            <div>
              <p style={{ fontWeight: 600, color: 'var(--success)' }}>📄 {file.name}</p>
              <p className="text-sm text-muted mt-sm">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div>
              <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Drop your CSV file here</p>
              <p className="text-sm text-muted mt-sm">or click to browse</p>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-md" style={{ color: 'var(--error)' }}>
            <HiOutlineExclamationTriangle /> {error}
          </div>
        )}

        <div style={{ marginTop: 24, padding: 16, background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
          <p className="text-sm" style={{ color: 'var(--warning)' }}>
            ⚠️ The import engine will automatically detect data anomalies including:
          </p>
          <ul className="text-sm text-muted" style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>Duplicate entries</li>
            <li>Missing fields (payer, currency)</li>
            <li>Settlements disguised as expenses</li>
            <li>Percentage splits that don't sum to 100%</li>
            <li>Members included after leaving</li>
            <li>Ambiguous dates and amount formatting</li>
          </ul>
        </div>

        <button
          className="btn btn-primary btn-lg w-full mt-lg"
          onClick={handleUpload}
          disabled={!file || !groupId || uploading}
        >
          {uploading ? 'Analyzing CSV...' : 'Upload & Analyze'}
        </button>
      </div>
    </div>
  );
}
