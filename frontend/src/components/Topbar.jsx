// Topbar.jsx — Esri-style header bar
import styles from './Topbar.module.css'

export default function Topbar({ connected, lastRefresh, onRefresh }) {
  const time = lastRefresh
    ? lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—'

  return (
    <header className={styles.bar}>
      <div className={styles.left}>
        <div className={styles.logo}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"
              fill="currentColor"/>
          </svg>
        </div>
        <span className={styles.title}>OKW FieldSync</span>
        <span className={styles.divider}>/</span>
        <span className={styles.subtitle}>Lead Service Line Inventory</span>
        <span className={styles.pwsid}>PWSID: OK1020401</span>
      </div>

      <div className={styles.right}>
        <span className={styles.refreshTime}>Updated {time}</span>
        <button className={styles.refreshBtn} onClick={onRefresh} title="Refresh data">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
            <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"
              fill="currentColor"/>
          </svg>
          Refresh
        </button>
        <div className={`${styles.status} ${connected ? styles.connected : styles.offline}`}>
          <span className={styles.dot} />
          {connected ? 'CONNECTED' : 'OFFLINE'}
        </div>
      </div>
    </header>
  )
}