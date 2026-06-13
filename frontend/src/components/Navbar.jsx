import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HiOutlineHome, HiOutlineUserGroup, HiOutlineDocumentArrowUp, HiOutlineArrowRightOnRectangle } from 'react-icons/hi2';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname.startsWith(path);

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/dashboard" className="navbar-brand">
          <div className="logo-icon">💰</div>
          FairShare
        </Link>

        <ul className="navbar-nav">
          <li>
            <Link to="/dashboard" className={isActive('/dashboard') ? 'active' : ''}>
              <HiOutlineHome style={{ marginRight: 4, verticalAlign: 'middle' }} />
              Dashboard
            </Link>
          </li>
          <li>
            <Link to="/groups" className={isActive('/groups') ? 'active' : ''}>
              <HiOutlineUserGroup style={{ marginRight: 4, verticalAlign: 'middle' }} />
              Groups
            </Link>
          </li>
          <li>
            <Link to="/import" className={isActive('/import') ? 'active' : ''}>
              <HiOutlineDocumentArrowUp style={{ marginRight: 4, verticalAlign: 'middle' }} />
              Import CSV
            </Link>
          </li>
        </ul>

        <div className="nav-user">
          <div className="nav-avatar">{user?.display_name?.[0] || '?'}</div>
          <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)' }}>
            {user?.display_name}
          </span>
          <button onClick={logout} className="btn btn-ghost btn-sm" title="Logout">
            <HiOutlineArrowRightOnRectangle />
          </button>
        </div>
      </div>
    </nav>
  );
}
