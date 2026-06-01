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

export default function Sidebar({ activePage, onNavigate }) {
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
          <div className={styles.avatar}>AM</div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>A. Mutu</span>
            <span className={styles.userRole}>Field Inspector</span>
          </div>
          <span className={styles.onlineDot} />
        </div>
        <div className={styles.orgInfo}>
          <span className={styles.orgLabel}>Oklahoma City Public Works</span>
          <span className={styles.orgPwsid}>PWSID: OK1020401</span>
        </div>
      </div>
    </aside>
  )
}