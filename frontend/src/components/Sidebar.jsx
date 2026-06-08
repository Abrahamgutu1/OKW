// Sidebar.jsx — Enterprise left nav
import styles from './Sidebar.module.css'

const NAV = [
  { id: 'dashboard',  label: 'Dashboard',    icon: '▦',  group: 'main' },
  { id: 'inventory',  label: 'Inventory',    icon: '⊞',  group: 'main' },
  { id: 'map',        label: 'Map View',     icon: '◎',  group: 'main' },
  { id: 'inspection', label: 'Inspections',  icon: '⊡',  group: 'main' },
  { id: 'reports',    label: 'Reports',      icon: '≡',  group: 'compliance' },
  { id: 'settings',   label: 'Settings',     icon: '⚙',  group: 'system' },
]

const GROUPS = {
  main:       'Operations',
  compliance: 'Compliance',
  system:     'System',
}

export default function Sidebar({ activePage, onNavigate, user, onLogout }) {
  const grouped = {}
  NAV.forEach(item => {
    if (!grouped[item.group]) grouped[item.group] = []
    grouped[item.group].push(item)
  })

  return (
    <aside className={styles.sidebar}>
      {/* Logo */}
      <div className={styles.logo}>
        <div className={styles.logoMark}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="8" r="4" fill="white" opacity="0.9"/>
            <path d="M4 20c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke="white" strokeWidth="2" strokeLinecap="round" opacity="0.7"/>
            <circle cx="12" cy="8" r="2" fill="var(--brand-500)"/>
          </svg>
        </div>
        <div className={styles.logoText}>
          <span className={styles.logoTitle}>FieldSync</span>
          <span className={styles.logoSub}>Lead Service Line</span>
        </div>
      </div>

      {/* Nav groups */}
      <nav className={styles.nav}>
        {Object.entries(grouped).map(([group, items]) => (
          <div key={group} className={styles.navGroup}>
            <span className={styles.navGroupLabel}>{GROUPS[group]}</span>
            {items.map(item => (
              <button
                key={item.id}
                className={`${styles.navItem} ${activePage === item.id ? styles.navActive : ''}`}
                onClick={() => onNavigate(item.id)}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <span className={styles.navLabel}>{item.label}</span>
                {item.id === 'inspection' &&
                  <span className={styles.navBadge}>3</span>
                }
              </button>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className={styles.sidebarFooter}>
        <div className={styles.userCard}>
          <div className={styles.avatar}>
            {user ? user.full_name.split(' ').map(n => n[0]).join('').slice(0,2).toUpperCase() : 'AM'}
          </div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>{user ? user.full_name : 'A. Mutu'}</span>
            <span className={styles.userRole}>{user ? user.role : 'Field Inspector'}</span>
          </div>
          <span className={styles.onlineDot} />
        </div>
        <div className={styles.orgInfo}>
          <span className={styles.orgLabel}>Oklahoma City Public Works</span>
          <span className={styles.orgPwsid}>PWSID: {user ? user.utility_id : 'OK1020401'}</span>
        </div>
        <button
          onClick={onLogout}
          style={{
            width: '100%', marginTop: 8, padding: '7px',
            background: 'rgba(220,38,38,0.08)',
            border: '1px solid rgba(220,38,38,0.2)',
            borderRadius: 6, color: '#f87171',
            fontSize: 11, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'inherit', letterSpacing: '0.04em'
          }}
        >
          Sign Out
        </button>
      </div>
    </aside>
  )
}