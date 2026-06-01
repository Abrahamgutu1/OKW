// AlertBanner.jsx — Critical compliance alerts
import { useState } from 'react'
import styles from './AlertBanner.module.css'

export default function AlertBanner({ records }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed || !records?.length) return null

  const suspects = records.filter(r => {
    const d = r.ai_distance
    return d !== null && d !== undefined && d < 0.35 &&
           r.user_verified_status === 'UNVERIFIED'
  })

  if (!suspects.length) return null

  return (
    <div className={styles.banner}>
      <div className={styles.left}>
        <div className={styles.iconWrap}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" fill="currentColor" opacity="0.2"/>
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div className={styles.text}>
          <strong>{suspects.length} unverified Lead Suspect {suspects.length === 1 ? 'record requires' : 'records require'} field inspection</strong>
          <span className={styles.sub}>
            &nbsp;— ODEQ LCRR compliance deadline requires verification within 45 days.
            Service lines: {suspects.slice(0,3).map(r => `SL-${r.service_line_id}`).join(', ')}
            {suspects.length > 3 ? ` +${suspects.length - 3} more` : ''}.
          </span>
        </div>
      </div>
      <div className={styles.actions}>
        <button className={styles.viewBtn}>View All →</button>
        <button className={styles.dismissBtn} onClick={() => setDismissed(true)}>✕</button>
      </div>
    </div>
  )
}