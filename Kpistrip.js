// KPIStrip.jsx — Esri-style indicator widgets
import styles from './KPIStrip.module.css'

function Indicator({ value, label, sub, color, icon }) {
  return (
    <div className={`${styles.card} ${styles[color]}`}>
      <div className={styles.iconRow}>
        <span className={styles.icon}>{icon}</span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.value}>{value}</div>
      {sub && <div className={styles.sub}>{sub}</div>}
      <div className={`${styles.bar} ${styles[`bar_${color}`]}`} />
    </div>
  )
}

export default function KPIStrip({ kpis }) {
  if (!kpis) return null
  return (
    <div className={styles.strip}>
      <Indicator value={kpis.total}    label="TOTAL RECORDS"    sub={`${kpis.lines} service lines`}    color="blue"  icon="📋" />
      <Indicator value={kpis.suspect}  label="LEAD SUSPECT"     sub="AI distance < 0.35"               color="red"   icon="⚠️" />
      <Indicator value={kpis.verified} label="VERIFIED"         sub="Inspector sign-off"               color="green" icon="✅" />
      <Indicator value={kpis.pending}  label="PENDING REVIEW"   sub="Awaiting verification"            color="amber" icon="🕐" />
      <Indicator value={kpis.has_photo}label="PHOTO RECORDS"    sub="Field images on record"           color="teal"  icon="📷" />
    </div>
  )
}