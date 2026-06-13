import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';

export default function ImportReport() {
  const { sessionId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/import/${sessionId}/report/`)
      .then(res => setReport(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!report) return <p>Report not found</p>;

  const { session, summary, anomalies } = report;

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title">Import Report</h1>
        <p className="page-subtitle">{session.filename}</p>
      </div>

      {/* Summary */}
      <div className="card mb-lg">
        <h2 className="card-title" style={{ marginBottom: 16 }}>Summary</h2>
        <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-value">{session.total_rows}</div>
            <div className="stat-label">Total Rows</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--success)' }}>{session.imported_rows}</div>
            <div className="stat-label">Imported</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--warning)' }}>{session.skipped_rows}</div>
            <div className="stat-label">Skipped</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--info)' }}>{summary.auto_fixed}</div>
            <div className="stat-label">Auto-Fixed</div>
          </div>
        </div>

        <table className="data-table mt-md">
          <tbody>
            <tr><td>Status</td><td><span className="badge badge-success">{session.status}</span></td></tr>
            <tr><td>Uploaded</td><td>{new Date(session.uploaded_at).toLocaleString()}</td></tr>
            <tr><td>Completed</td><td>{session.completed_at ? new Date(session.completed_at).toLocaleString() : 'N/A'}</td></tr>
            <tr><td>Info anomalies</td><td>{summary.info}</td></tr>
            <tr><td>Warnings</td><td>{summary.warning}</td></tr>
            <tr><td>Errors</td><td>{summary.error}</td></tr>
            <tr><td>Critical</td><td>{summary.critical}</td></tr>
          </tbody>
        </table>
      </div>

      {/* Detailed Anomaly Log */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: 16 }}>Anomaly Log ({anomalies.length} issues detected)</h2>

        {anomalies.map((a) => (
          <div key={a.id} className={`anomaly-card severity-${a.severity}`}>
            <div className="anomaly-header">
              <div className="anomaly-meta">
                <span className={`badge badge-${a.severity === 'critical' ? 'critical' : a.severity}`}>
                  {a.severity}
                </span>
                <span>Row {a.row_number}</span>
                <span>·</span>
                <span>{a.anomaly_type.replace(/_/g, ' ')}</span>
              </div>
              <span className={`badge ${
                a.user_action === 'auto_fixed' ? 'badge-info' :
                a.user_action === 'user_approved' ? 'badge-success' :
                a.user_action === 'skipped' ? 'badge-warning' : 'badge-error'
              }`}>
                {a.user_action.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="anomaly-description">{a.description}</div>
            {a.ai_description && (
              <div className="text-sm text-muted" style={{ fontStyle: 'italic', marginTop: 4 }}>
                🤖 AI: {a.ai_description}
              </div>
            )}
            {a.original_value && (
              <div className="text-sm mt-sm">
                <span className="text-muted">Original: </span>
                <code style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: 4 }}>
                  {a.original_value}
                </code>
                {a.corrected_value && (
                  <>
                    <span className="text-muted"> → </span>
                    <code style={{ background: 'var(--success-bg)', padding: '2px 6px', borderRadius: 4, color: 'var(--success)' }}>
                      {a.corrected_value}
                    </code>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex justify-between mt-lg">
        <Link to="/dashboard" className="btn btn-secondary">Back to Dashboard</Link>
        <Link to={`/groups/`} className="btn btn-primary">View Groups</Link>
      </div>
    </div>
  );
}
