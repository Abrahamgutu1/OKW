// EvidenceList.jsx — Esri list widget panel
import styles from './EvidenceList.module.css'

function classifyRecord(record) {
  const s = record.user_verified_status || ''
  if (s === 'MANUALLY_CONFIRMED_LEAD') return { label: 'LEAD',     color: 'red' }
  if (s === 'MANUALLY_CONFIRMED_SAFE') return { label: 'SAFE',     color: 'green' }
  const d = record.ai_distance
  if (d !== null && d !== undefined && d < 0.35) return { label: 'SUSPECT', color: 'red' }
  if (d !== null && d !== undefined)              return { label: 'CLEAR',   color: 'green' }
  return { label: 'UNKNOWN', color: 'amber' }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })
}

export default function EvidenceList({ records, selectedId, onSelect }) {
  if (!records) return null

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>📋 Service Line Inventory</span>
        <span className={styles.count}>{records.length}</span>
      </div>

      <div className={styles.list}>
        {records.map(rec => {
          const { label, color } = classifyRecord(rec)
          const isActive = selectedId === rec.evidence_id
          return (
            <button
              key={rec.evidence_id}
              className={`${styles.row} ${isActive ? styles.active : ''}`}
              onClick={() => onSelect(rec)}
            >
              <div className={`${styles.dot} ${styles[`dot_${color}`]}`} />
              <div className={styles.info}>
                <div className={styles.ids}>
                  <span className={`${styles.slId} mono`}>SL-{rec.service_line_id}</span>
                  <span className={styles.evId}>EV-{rec.evidence_id}</span>
                </div>
                <div className={styles.meta}>
                  <span>{formatDate(rec.upload_date)}</span>
                  {rec.ai_distance !== null && rec.ai_distance !== undefined &&
                    <span className="mono">{Number(rec.ai_distance).toFixed(4)}</span>
                  }
                </div>
              </div>
              <span className={`${styles.badge} ${styles[`badge_${color}`]}`}>{label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}