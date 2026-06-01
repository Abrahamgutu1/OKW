// KPICards.jsx — Cityworks-style metric cards
import styles from './KPICards.module.css'

function Card({ value, label, sub, color, icon, trend }) {
  return (
    <div className={`${styles.card} ${styles[color]}`}>
      <div className={styles.top}>
        <div className={styles.iconBox}>{icon}</div>
        {trend && (
          <span className={`${styles.trend} ${trend > 0 ? styles.trendUp : styles.trendDown}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className={styles.value}>{value ?? '—'}</div>
      <div className={styles.label}>{label}</div>
      {sub && <div className={styles.sub}>{sub}</div>}
    </div>
  )
}

export default function KPICards({ kpis }) {
  return (
    <div className={styles.grid}>
      <Card value={kpis?.total}     label="Total Records"       sub={`${kpis?.lines ?? 0} service lines`}  color="blue"    icon="📋" />
      <Card value={kpis?.suspect}   label="Lead Suspect"        sub="AI distance < 0.35"                   color="danger"  icon="⚠️"  trend={0} />
      <Card value={kpis?.verified}  label="Inspector Verified"  sub="Signed off on record"                 color="success" icon="✅" />
      <Card value={kpis?.pending}   label="Pending Review"      sub="Awaiting field inspection"            color="warn"    icon="🕐" />
      <Card value={kpis?.has_photo} label="Photo Evidence"      sub="Images on record"                     color="teal"    icon="📷" />
    </div>
  )
}