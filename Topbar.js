// Topbar.jsx — Enterprise header with breadcrumb + search
import styles from './Topbar.module.css'

const PAGE_TITLES = {
  dashboard:  { label: 'Dashboard',   crumb: ['Home', 'Dashboard'] },
  inventory:  { label: 'Inventory',   crumb: ['Home', 'Inventory'] },
  map:        { label: 'Map View',    crumb: ['Home', 'Map View'] },
  inspection: { label: 'Inspections', crumb: ['Home', 'Inspections'] },
  reports:    { label: 'Reports',     crumb: ['Home', 'Compliance', 'Reports'] },
  settings:   { label: 'Settings',   crumb: ['Home', 'Settings'] },
}

export default function Topbar({ page, connected, lastRefresh, onRefresh, alertCount }) {
  const meta = PAGE_TITLES[page] || PAGE_TITLES.dashboard
  const time = lastRefresh
    ? lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null

  return (
    <header className={styles.bar}>
      <div className={styles.left}>
        {/* Breadcrumb */}
        <nav className={styles.breadcrumb}>
          {meta.crumb.map((c, i) => (
            <span key={i} className={styles.crumbItem}>
              {i > 0 && <span className={styles.crumbSep}>/</span>}
              <span className={i === meta.crumb.length - 1 ? styles.crumbActive : styles.crumbLink}>
                {c}
              </span>
            </span>
          ))}
        </nav>
        <h1 className={styles.pageTitle}>{meta.label}</h1>
      </div>

      <div className={styles.center}>
        <div className={styles.searchBox}>
          <svg className={styles.searchIcon} width="13" height="13" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2"/>
            <path d="m16.5 16.5 4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <input
            type="text"
            placeholder="Search service lines, evidence IDs…"
            className={styles.searchInput}
          />
          <kbd className={styles.kbd}>⌘K</kbd>
        </div>
      </div>

      <div className={styles.right}>
        {/* Alert bell */}
        {alertCount > 0 && (
          <button className={styles.alertBtn}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span className={styles.alertBubble}>{alertCount}</span>
          </button>
        )}

        {time && (
          <span className={styles.syncTime}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" style={{marginRight:3}}>
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            {time}
          </span>
        )}

        <button className={styles.refreshBtn} onClick={onRefresh}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
            <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Refresh
        </button>

        <div className={`${styles.connBadge} ${connected ? styles.connOk : styles.connOff}`}>
          <span className={styles.connDot} />
          {connected ? 'Live' : 'Offline'}
        </div>
      </div>
    </header>
  )
}