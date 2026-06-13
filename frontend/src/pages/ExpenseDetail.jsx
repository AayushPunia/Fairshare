import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';

export default function ExpenseDetail() {
  const { id } = useParams();
  const [expense, setExpense] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/expenses/${id}/`)
      .then(res => setExpense(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!expense) return <p>Expense not found</p>;

  const isUSD = expense.currency === 'USD';

  return (
    <div className="animate-fadeIn" style={{ maxWidth: 600, margin: '0 auto' }}>
      <Link to={`/groups/${expense.group}`} className="text-sm" style={{ display: 'block', marginBottom: 16 }}>
        ← Back to group
      </Link>

      <div className="card">
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 800, color: 'var(--text-primary)' }}>
            {expense.description}
          </h1>
          {expense.is_settlement && <span className="badge badge-info mt-sm">Settlement</span>}
        </div>

        <div className="stat-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: 20 }}>
          <div className="stat-card">
            <div className="stat-label">Amount</div>
            <div className="stat-value" style={{ color: 'var(--accent-secondary)' }}>
              {isUSD ? '$' : '₹'}{parseFloat(expense.amount).toLocaleString()}
            </div>
            {isUSD && <div className="text-sm text-muted">≈ ₹{parseFloat(expense.amount_inr).toLocaleString()}</div>}
          </div>
          <div className="stat-card">
            <div className="stat-label">Paid By</div>
            <div className="stat-value" style={{ fontSize: 'var(--font-lg)' }}>{expense.paid_by?.display_name}</div>
          </div>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Detail</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Date</td><td>{expense.date}</td></tr>
            <tr><td>Split Type</td><td><span className="badge badge-info">{expense.split_type}</span></td></tr>
            <tr><td>Currency</td><td>{expense.currency}</td></tr>
            {isUSD && <tr><td>Exchange Rate</td><td>1 USD = ₹{expense.exchange_rate}</td></tr>}
            {expense.notes && <tr><td>Notes</td><td>{expense.notes}</td></tr>}
          </tbody>
        </table>

        <h3 style={{ marginTop: 24, marginBottom: 12, fontWeight: 700 }}>Split Breakdown</h3>
        <p className="text-sm text-muted mb-md">
          This is exactly how ₹{parseFloat(expense.amount_inr).toLocaleString()} is divided:
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Person</th>
              <th>Share (₹)</th>
              {expense.split_type === 'percentage' && <th>%</th>}
              {expense.split_type === 'share' && <th>Units</th>}
            </tr>
          </thead>
          <tbody>
            {expense.splits?.map(split => (
              <tr key={split.id}>
                <td style={{ fontWeight: 600 }}>{split.user?.display_name}</td>
                <td>₹{parseFloat(split.share_amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                {expense.split_type === 'percentage' && <td>{split.share_percentage}%</td>}
                {expense.split_type === 'share' && <td>{split.share_units}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
