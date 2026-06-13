import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../api/client';
import { HiOutlinePlusCircle, HiOutlineBanknotes, HiOutlineArrowsRightLeft, HiOutlineUserPlus } from 'react-icons/hi2';

export default function GroupDetail() {
  const { id } = useParams();
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState({});
  const [settlements, setSuggested] = useState([]);
  const [tab, setTab] = useState('expenses');
  const [loading, setLoading] = useState(true);
  const [showAddMember, setShowAddMember] = useState(false);
  const [showAddExpense, setShowAddExpense] = useState(false);
  const [allUsers, setAllUsers] = useState([]);
  const [addMemberData, setAddMemberData] = useState({ user_id: '', joined_at: '' });
  const [expenseForm, setExpenseForm] = useState({
    description: '', amount: '', currency: 'INR', split_type: 'equal',
    date: new Date().toISOString().split('T')[0], notes: '', paid_by_id: '',
    participants: [],
  });
  const [settleForm, setSettleForm] = useState({ from_user_id: '', to_user_id: '', amount: '', date: new Date().toISOString().split('T')[0] });
  const [showSettle, setShowSettle] = useState(false);

  useEffect(() => {
    loadAll();
  }, [id]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [groupRes, expRes, balRes, settleRes, usersRes] = await Promise.all([
        api.get(`/groups/${id}/`),
        api.get(`/expenses/group/${id}/`),
        api.get(`/expenses/group/${id}/balances/`),
        api.get(`/expenses/group/${id}/settlements/suggest/`),
        api.get('/auth/users/'),
      ]);
      setGroup(groupRes.data);
      setExpenses(expRes.data.results || expRes.data);
      setBalances(balRes.data);
      setSuggested(settleRes.data);
      setAllUsers(usersRes.data.results || usersRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/groups/${id}/members/`, addMemberData);
      setShowAddMember(false);
      setAddMemberData({ user_id: '', joined_at: '' });
      loadAll();
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to add member');
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!confirm('Set this member as left?')) return;
    try {
      await api.patch(`/groups/${id}/members/${memberId}/`, {
        left_at: new Date().toISOString().split('T')[0], is_active: false,
      });
      loadAll();
    } catch (err) {
      alert('Failed to update member');
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    const members = group.members.filter(m => m.is_active);
    const participants = members.map(m => ({ user_id: m.user.id }));
    try {
      await api.post(`/expenses/group/${id}/`, {
        ...expenseForm,
        paid_by_id: parseInt(expenseForm.paid_by_id),
        amount: parseFloat(expenseForm.amount),
        participants,
      });
      setShowAddExpense(false);
      setExpenseForm({ description: '', amount: '', currency: 'INR', split_type: 'equal', date: new Date().toISOString().split('T')[0], notes: '', paid_by_id: '', participants: [] });
      loadAll();
    } catch (err) {
      alert(JSON.stringify(err.response?.data) || 'Failed');
    }
  };

  const handleSettle = async (e) => {
    e.preventDefault();
    try {
      await api.post('/expenses/settlements/', {
        group_id: parseInt(id),
        from_user_id: parseInt(settleForm.from_user_id),
        to_user_id: parseInt(settleForm.to_user_id),
        amount: parseFloat(settleForm.amount),
        date: settleForm.date,
      });
      setShowSettle(false);
      loadAll();
    } catch (err) {
      alert('Failed to record settlement');
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;
  if (!group) return <p>Group not found</p>;

  const members = group.members || [];
  const balanceEntries = Object.values(balances);

  return (
    <div className="animate-fadeIn">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">{group.name}</h1>
          <p className="page-subtitle">{group.description || `${members.length} members`}</p>
        </div>
        <div className="flex gap-sm">
          <button className="btn btn-secondary btn-sm" onClick={() => setShowAddMember(!showAddMember)}>
            <HiOutlineUserPlus /> Add Member
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setShowAddExpense(!showAddExpense)}>
            <HiOutlinePlusCircle /> Add Expense
          </button>
        </div>
      </div>

      {/* Add Member Form */}
      {showAddMember && (
        <div className="card mb-lg animate-fadeIn">
          <h3 className="card-title" style={{ marginBottom: 12 }}>Add Member</h3>
          <form onSubmit={handleAddMember} className="form-row">
            <div className="form-group">
              <label className="form-label">User</label>
              <select className="form-select" value={addMemberData.user_id}
                onChange={e => setAddMemberData({...addMemberData, user_id: parseInt(e.target.value)})}>
                <option value="">Select user...</option>
                {allUsers.filter(u => !members.some(m => m.user.id === u.id)).map(u => (
                  <option key={u.id} value={u.id}>{u.display_name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Joined Date</label>
              <input type="date" className="form-input" value={addMemberData.joined_at}
                onChange={e => setAddMemberData({...addMemberData, joined_at: e.target.value})} required />
            </div>
            <button type="submit" className="btn btn-success btn-sm">Add</button>
          </form>
        </div>
      )}

      {/* Add Expense Form */}
      {showAddExpense && (
        <div className="card mb-lg animate-fadeIn">
          <h3 className="card-title" style={{ marginBottom: 12 }}>Add Expense</h3>
          <form onSubmit={handleAddExpense}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Description</label>
                <input className="form-input" value={expenseForm.description}
                  onChange={e => setExpenseForm({...expenseForm, description: e.target.value})} required />
              </div>
              <div className="form-group">
                <label className="form-label">Amount</label>
                <input type="number" step="0.01" className="form-input" value={expenseForm.amount}
                  onChange={e => setExpenseForm({...expenseForm, amount: e.target.value})} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Paid By</label>
                <select className="form-select" value={expenseForm.paid_by_id}
                  onChange={e => setExpenseForm({...expenseForm, paid_by_id: e.target.value})} required>
                  <option value="">Select...</option>
                  {members.filter(m => m.is_active).map(m => (
                    <option key={m.user.id} value={m.user.id}>{m.user.display_name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Date</label>
                <input type="date" className="form-input" value={expenseForm.date}
                  onChange={e => setExpenseForm({...expenseForm, date: e.target.value})} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Currency</label>
                <select className="form-select" value={expenseForm.currency}
                  onChange={e => setExpenseForm({...expenseForm, currency: e.target.value})}>
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Split Type</label>
                <select className="form-select" value={expenseForm.split_type}
                  onChange={e => setExpenseForm({...expenseForm, split_type: e.target.value})}>
                  <option value="equal">Equal</option>
                  <option value="unequal">Unequal</option>
                  <option value="percentage">Percentage</option>
                  <option value="share">By Shares</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Notes (optional)</label>
              <input className="form-input" value={expenseForm.notes}
                onChange={e => setExpenseForm({...expenseForm, notes: e.target.value})} />
            </div>
            <button type="submit" className="btn btn-primary">Save Expense</button>
          </form>
        </div>
      )}

      {/* Members */}
      <div className="card mb-lg">
        <h3 className="card-title" style={{ marginBottom: 12 }}>Members</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {members.map((m) => (
            <div key={m.id} className="badge" style={{
              padding: '6px 14px',
              background: m.is_active ? 'var(--success-bg)' : 'var(--bg-tertiary)',
              color: m.is_active ? 'var(--success)' : 'var(--text-muted)',
              border: `1px solid ${m.is_active ? 'rgba(0,184,148,0.2)' : 'var(--border-primary)'}`,
              cursor: 'pointer',
            }} onClick={() => !m.is_active ? null : handleRemoveMember(m.id)} title={m.is_active ? 'Click to mark as left' : `Left: ${m.left_at}`}>
              {m.user.display_name}
              {!m.is_active && <span style={{ fontSize: '0.65rem', marginLeft: 4 }}>(left {m.left_at})</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-sm mb-lg">
        {['expenses', 'balances', 'settlements'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`btn ${tab === t ? 'btn-primary' : 'btn-ghost'} btn-sm`}>
            {t === 'expenses' && <HiOutlineBanknotes />}
            {t === 'balances' && '📊'}
            {t === 'settlements' && <HiOutlineArrowsRightLeft />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Expenses Tab */}
      {tab === 'expenses' && (
        <div>
          {expenses.length === 0 ? (
            <div className="empty-state">
              <p className="empty-state-title">No expenses yet</p>
              <p>Add your first expense or import from CSV</p>
            </div>
          ) : (
            <div>
              {expenses.map((exp, i) => (
                <Link to={`/expenses/${exp.id}`} key={exp.id} style={{ textDecoration: 'none' }}
                  className={`animate-fadeIn stagger-${Math.min(i+1, 5)}`}>
                  <div className="card" style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {exp.description}
                        {exp.is_settlement && <span className="badge badge-info" style={{ marginLeft: 8 }}>Settlement</span>}
                      </div>
                      <div className="text-sm text-muted">
                        {exp.date} · Paid by {exp.paid_by?.display_name} · {exp.split_type}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, color: 'var(--accent-secondary)', fontSize: 'var(--font-lg)' }}>
                        {exp.currency === 'USD' ? '$' : '₹'}{parseFloat(exp.amount).toLocaleString()}
                      </div>
                      {exp.currency === 'USD' && (
                        <div className="text-sm text-muted">≈ ₹{parseFloat(exp.amount_inr).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Balances Tab */}
      {tab === 'balances' && (
        <div>
          <div className="card-grid">
            {balanceEntries.map((b, i) => {
              const net = parseFloat(b.net_balance);
              return (
                <div key={b.user.id} className={`glass-card animate-fadeIn stagger-${i+1}`}>
                  <div className="flex items-center gap-md" style={{ marginBottom: 12 }}>
                    <div className="nav-avatar">{b.user.display_name[0]}</div>
                    <h3 style={{ fontWeight: 700 }}>{b.user.display_name}</h3>
                  </div>
                  <div className={`balance-amount ${net > 0 ? 'balance-positive' : net < 0 ? 'balance-negative' : 'balance-zero'}`}>
                    {net > 0 ? '+' : ''}{net === 0 ? 'Settled' : `₹${Math.abs(net).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                  </div>
                  <p className="text-sm text-muted mt-sm">
                    {net > 0 ? 'Gets back' : net < 0 ? 'Owes' : 'All settled up'}
                  </p>
                  <div className="mt-md" style={{ borderTop: '1px solid var(--border-primary)', paddingTop: 12 }}>
                    <p className="text-sm text-muted">Total paid: ₹{parseFloat(b.total_paid).toLocaleString()}</p>
                    <p className="text-sm text-muted">Total share: ₹{parseFloat(b.total_owed).toLocaleString()}</p>
                  </div>
                  {/* Drill-down: expense list */}
                  {b.expenses_paid.length > 0 && (
                    <details style={{ marginTop: 8 }}>
                      <summary className="text-sm" style={{ cursor: 'pointer', color: 'var(--accent-secondary)' }}>
                        Expenses paid ({b.expenses_paid.length})
                      </summary>
                      <ul style={{ listStyle: 'none', marginTop: 4 }}>
                        {b.expenses_paid.map(e => (
                          <li key={e.id} className="text-sm text-muted" style={{ padding: '2px 0' }}>
                            {e.description}: ₹{parseFloat(e.amount_inr).toLocaleString()} ({e.date})
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                  {b.expenses_shared.length > 0 && (
                    <details style={{ marginTop: 4 }}>
                      <summary className="text-sm" style={{ cursor: 'pointer', color: 'var(--accent-secondary)' }}>
                        Share in expenses ({b.expenses_shared.length})
                      </summary>
                      <ul style={{ listStyle: 'none', marginTop: 4 }}>
                        {b.expenses_shared.map(e => (
                          <li key={e.id} className="text-sm text-muted" style={{ padding: '2px 0' }}>
                            {e.description}: ₹{parseFloat(e.share_amount).toLocaleString()} (paid by {e.paid_by})
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Settlements Tab */}
      {tab === 'settlements' && (
        <div>
          <div className="flex items-center justify-between mb-md">
            <h3 className="card-title">Suggested Settlements</h3>
            <button className="btn btn-success btn-sm" onClick={() => setShowSettle(!showSettle)}>
              Record Payment
            </button>
          </div>

          {showSettle && (
            <div className="card mb-lg animate-fadeIn">
              <form onSubmit={handleSettle} className="form-row">
                <div className="form-group">
                  <label className="form-label">From</label>
                  <select className="form-select" value={settleForm.from_user_id}
                    onChange={e => setSettleForm({...settleForm, from_user_id: e.target.value})} required>
                    <option value="">Select...</option>
                    {members.filter(m => m.is_active).map(m => (
                      <option key={m.user.id} value={m.user.id}>{m.user.display_name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">To</label>
                  <select className="form-select" value={settleForm.to_user_id}
                    onChange={e => setSettleForm({...settleForm, to_user_id: e.target.value})} required>
                    <option value="">Select...</option>
                    {members.filter(m => m.is_active).map(m => (
                      <option key={m.user.id} value={m.user.id}>{m.user.display_name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Amount (₹)</label>
                  <input type="number" step="0.01" className="form-input" value={settleForm.amount}
                    onChange={e => setSettleForm({...settleForm, amount: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input type="date" className="form-input" value={settleForm.date}
                    onChange={e => setSettleForm({...settleForm, date: e.target.value})} required />
                </div>
                <button type="submit" className="btn btn-success btn-sm">Record</button>
              </form>
            </div>
          )}

          {settlements.length === 0 ? (
            <div className="empty-state">
              <p className="empty-state-title">🎉 All settled!</p>
              <p>No outstanding balances</p>
            </div>
          ) : (
            <div>
              {settlements.map((s, i) => (
                <div key={i} className={`settlement-item animate-fadeIn stagger-${i+1}`}>
                  <div className="nav-avatar" style={{ background: 'var(--error-bg)', color: 'var(--error)' }}>
                    {s.from[0]}
                  </div>
                  <span style={{ fontWeight: 600 }}>{s.from}</span>
                  <span className="settlement-arrow">→</span>
                  <div className="nav-avatar">{s.to[0]}</div>
                  <span style={{ fontWeight: 600 }}>{s.to}</span>
                  <span className="settlement-amount">₹{parseFloat(s.amount).toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
