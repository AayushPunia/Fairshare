import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { HiOutlineCheckCircle, HiOutlineXCircle, HiOutlinePencilSquare } from 'react-icons/hi2';

export default function ImportReview() {
  const { sessionId } = useParams();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [resolutions, setResolutions] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    api.get(`/import/${sessionId}/`)
      .then(res => {
        setSession(res.data);
        // Pre-set auto-resolved items
        const initial = {};
        res.data.anomalies?.forEach(a => {
          if (a.auto_resolved) {
            initial[a.id] = { action: 'approve' };
          }
        });
        setResolutions(initial);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleResolve = (anomalyId, action) => {
    setResolutions(prev => ({
      ...prev,
      [anomalyId]: { action },
    }));
  };

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      // Submit resolutions
      const resolvedList = Object.entries(resolutions).map(([id, r]) => ({
        anomaly_id: parseInt(id),
        action: r.action,
        corrected_value: r.corrected_value || '',
      }));

      await api.post(`/import/${sessionId}/resolve/`, { resolutions: resolvedList });
      const res = await api.post(`/import/${sessionId}/confirm/`);
      navigate(`/import/${sessionId}/report`);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to confirm import');
    } finally {
      setConfirming(false);
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!session) return <p>Session not found</p>;

  const anomalies = session.anomalies || [];
  const criticalUnresolved = anomalies.filter(a => a.severity === 'critical' && !resolutions[a.id]);
  const allResolved = criticalUnresolved.length === 0;

  const severityOrder = { critical: 0, error: 1, warning: 2, info: 3 };
  const sortedAnomalies = [...anomalies].sort((a, b) =>
    (severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)
  );

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Review Import</h1>
        <p className="page-subtitle">
          {session.filename} — {session.total_rows} rows, {anomalies.length} anomalies detected
        </p>
      </div>

      {/* Summary Stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{session.total_rows}</div>
          <div className="stat-label">Total Rows</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--info)' }}>
            {anomalies.filter(a => a.severity === 'info').length}
          </div>
          <div className="stat-label">Auto-Fixed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--warning)' }}>
            {anomalies.filter(a => a.severity === 'warning').length}
          </div>
          <div className="stat-label">Warnings</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#ff6b6b' }}>
            {anomalies.filter(a => a.severity === 'critical' || a.severity === 'error').length}
          </div>
          <div className="stat-label">Critical</div>
        </div>
      </div>

      {/* Anomaly List */}
      <h2 className="card-title mb-md">Anomalies ({anomalies.length})</h2>
      <p className="text-sm text-muted mb-lg">
        Review each anomaly below. Critical issues must be resolved before importing.
        Meera's request: "I want to approve anything the app deletes or changes."
      </p>

      {sortedAnomalies.map((anomaly, i) => {
        const resolution = resolutions[anomaly.id];
        const isResolved = resolution || anomaly.auto_resolved;

        return (
          <div
            key={anomaly.id}
            className={`anomaly-card severity-${anomaly.severity} animate-fadeIn stagger-${Math.min(i+1, 5)}`}
            style={isResolved ? { opacity: 0.7 } : {}}
          >
            <div className="anomaly-header">
              <div className="anomaly-meta">
                <span className={`badge badge-${anomaly.severity === 'critical' ? 'critical' : anomaly.severity}`}>
                  {anomaly.severity.toUpperCase()}
                </span>
                <span>Row {anomaly.row_number}</span>
                <span>·</span>
                <span>{anomaly.anomaly_type.replace(/_/g, ' ')}</span>
              </div>
              {isResolved && (
                <span className="badge badge-success">
                  ✓ {resolution?.action || 'auto-fixed'}
                </span>
              )}
            </div>

            <div className="anomaly-description">
              {anomaly.ai_description || anomaly.description}
            </div>

            {anomaly.original_value && (
              <div className="text-sm" style={{ marginBottom: 8 }}>
                <span className="text-muted">Original: </span>
                <code style={{ background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: 4 }}>
                  {anomaly.original_value}
                </code>
                {anomaly.corrected_value && (
                  <>
                    <span className="text-muted"> → </span>
                    <code style={{ background: 'var(--success-bg)', padding: '2px 6px', borderRadius: 4, color: 'var(--success)' }}>
                      {anomaly.corrected_value}
                    </code>
                  </>
                )}
              </div>
            )}

            {!anomaly.auto_resolved && (
              <div className="anomaly-actions">
                <button
                  className={`btn btn-sm ${resolution?.action === 'approve' ? 'btn-success' : 'btn-ghost'}`}
                  onClick={() => handleResolve(anomaly.id, 'approve')}
                >
                  <HiOutlineCheckCircle /> Approve
                </button>
                <button
                  className={`btn btn-sm ${resolution?.action === 'skip' ? 'btn-danger' : 'btn-ghost'}`}
                  onClick={() => handleResolve(anomaly.id, 'skip')}
                >
                  <HiOutlineXCircle /> Skip Row
                </button>
              </div>
            )}
          </div>
        );
      })}

      {/* Confirm Button */}
      <div style={{ position: 'sticky', bottom: 0, background: 'var(--bg-primary)', padding: '16px 0', borderTop: '1px solid var(--border-primary)' }}>
        <div className="flex items-center justify-between">
          <div>
            {!allResolved && (
              <p className="text-sm" style={{ color: 'var(--error)' }}>
                ⚠️ {criticalUnresolved.length} critical anomalies must be resolved
              </p>
            )}
          </div>
          <button
            className="btn btn-primary btn-lg"
            onClick={handleConfirm}
            disabled={!allResolved || confirming}
          >
            {confirming ? 'Importing...' : `Confirm Import (${session.total_rows} rows)`}
          </button>
        </div>
      </div>
    </div>
  );
}
