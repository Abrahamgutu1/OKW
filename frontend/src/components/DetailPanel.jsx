// DetailPanel.jsx — Cityworks-style record detail drawer
import { useState } from 'react'
import styles from './DetailPanel.module.css'

const INSPECTOR_PINS = {
  'PIN-9402': 'A. Mutu (Badge #402)',
  'PIN-1185': 'J. Doe (Badge #185)',
  'PIN-2365': 'S. Smith (Badge #365)',
}

function classify(record) {
  const s = record?.user_verified_status || ''
  if (s === 'MANUALLY_CONFIRMED_LEAD') return { label: 'Confirmed Lead',  cls: 'danger' }
  if (s === 'MANUALLY_CONFIRMED_SAFE') return { label: 'Confirmed Safe',  cls: 'success' }
  const d = record?.ai_distance
  if (d !== null && d !== undefined && d < 0.35) return { label: 'Lead Suspect', cls: 'danger' }
  if (d !== null && d !== undefined)              return { label: 'Clear',        cls: 'success' }
  return { label: 'Unknown', cls: 'warn' }
}

function getConfidence(d) {
  if (d === null || d === undefined) return null
  d = Number(d)
  if (d < 0.35) return (99.9 - (d / 0.35) * 34.9).toFixed(1)
  return (65 + ((Math.min(d,1) - 0.35) / 0.65) * 34.9).toFixed(1)
}

export default function DetailPanel({ record, onClose }) {
  const [pin,      setPin]      = useState('')
  const [decision, setDecision] = useState('MANUALLY_CONFIRMED_SAFE')
  const [msg,      setMsg]      = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [tab,      setTab]      = useState('details')

  if (!record) return null

  const { label, cls } = classify(record)
  const conf = getConfidence(record.ai_distance)

  async function handleAudit(e) {
    e.preventDefault()
    if (!INSPECTOR_PINS[pin]) { setMsg({ type: 'error', text: 'Invalid security token. Access denied.' }); return }
    setLoading(true)
    try {
      const res  = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ evidence_id: record.evidence_id, status: decision, inspector_pin: pin })
      })
      const json = await res.json()
      setMsg(res.ok
        ? { type: 'success', text: json.message }
        : { type: 'error',   text: json.detail || 'Server error' }
      )
      if (res.ok) setPin('')
    } catch {
      setMsg({ type: 'error', text: 'Network error — check API connection.' })
    } finally { setLoading(false) }
  }

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div className={styles.headerIds}>
            <span className={styles.evId}>EV-{record.evidence_id}</span>
            <span className={styles.separator}>·</span>
            <span className={styles.slId}>SL-{record.service_line_id}</span>
          </div>
          <button className={styles.closeBtn} onClick={onClose}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M18 6 6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </div>
        <div className={styles.headerStatus}>
          <span className={`badge badge-${cls}`}>
            {cls === 'danger' ? '●' : cls === 'success' ? '✓' : '○'} {label}
          </span>
          {conf && (
            <span className={styles.confidence}>{conf}% AI confidence</span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        {['details', 'photo', 'audit'].map(t => (
          <button
            key={t}
            className={`${styles.tab} ${tab === t ? styles.tabActive : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'details' ? '📊 Details' : t === 'photo' ? '📷 Photo' : '🔒 Audit'}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className={styles.body}>

        {/* Details tab */}
        {tab === 'details' && (
          <>
            {/* AI Score bar */}
            {record.ai_distance !== null && record.ai_distance !== undefined && (
              <div className={styles.scoreSection}>
                <div className={styles.scoreLabelRow}>
                  <span className={styles.scoreLabel}>PIPE_VISION_AI Vector Score</span>
                  <span className={`${styles.scoreNum} mono`}
                    style={{ color: record.ai_distance < 0.35 ? 'var(--danger-600)' : 'var(--success-600)' }}>
                    {Number(record.ai_distance).toFixed(4)}
                  </span>
                </div>
                <div className={styles.progressTrack}>
                  <div
                    className={styles.progressFill}
                    style={{
                      width: `${Math.min(Number(record.ai_distance) * 100, 100)}%`,
                      background: record.ai_distance < 0.35 ? 'var(--danger-600)' : 'var(--success-600)'
                    }}
                  />
                  <div className={styles.threshold} title="0.35 threshold" />
                </div>
                <div className={styles.progressLabels}>
                  <span>Lead (0.00)</span>
                  <span style={{color:'var(--warn-600)'}}>▲ 0.35</span>
                  <span>Safe (1.00)</span>
                </div>
              </div>
            )}

            {/* Attribute table */}
            <table className={styles.attrTable}>
              <tbody>
                {[
                  { label: 'Evidence ID',   value: `EV-${record.evidence_id}`,     mono: true },
                  { label: 'Service Line',  value: `SL-${record.service_line_id}`, mono: true },
                  { label: 'GPS Latitude',  value: record.gps_latitude?.toFixed(6), mono: true },
                  { label: 'GPS Longitude', value: record.gps_longitude?.toFixed(6), mono: true },
                  { label: 'Upload Date',   value: record.upload_date ? new Date(record.upload_date).toLocaleString() : '—' },
                  { label: 'Audit Status',  value: record.user_verified_status?.replace('MANUALLY_CONFIRMED_','') || 'UNVERIFIED',
                    color: record.user_verified_status?.includes('LEAD') ? 'var(--danger-600)' : record.user_verified_status?.includes('SAFE') ? 'var(--success-600)' : 'var(--gray-500)' },
                  { label: 'Inspector',     value: record.audited_by || 'Not yet verified' },
                  { label: 'AI Engine',     value: 'PIPE_VISION_AI · ResNet-50 v1-12', mono: true },
                ].map(row => (
                  <tr key={row.label} className={styles.attrRow}>
                    <td className={styles.attrLabel}>{row.label}</td>
                    <td className={`${styles.attrValue} ${row.mono ? 'mono' : ''}`}
                      style={row.color ? { color: row.color, fontWeight: 600 } : {}}>
                      {row.value ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {/* Photo tab */}
        {tab === 'photo' && (
          <div className={styles.photoSection}>
            {record.photo_url && record.photo_url.startsWith('http') ? (
              <>
                <img src={record.photo_url} alt="Field inspection" className={styles.photo} />
                <div className={styles.photoMeta}>
                  <span className={styles.photoLabel}>Field Inspection Photo</span>
                  <a href={record.photo_url} target="_blank" rel="noreferrer" className={styles.photoLink}>
                    Open original ↗
                  </a>
                </div>
              </>
            ) : (
              <div className={styles.noPhoto}>
                <div style={{fontSize: '2.5rem', marginBottom: 8}}>📷</div>
                <p>No photo on record for this evidence entry</p>
                <p style={{fontSize:11, marginTop:4, color:'var(--gray-400)'}}>
                  Capture a field photo using the iOS app to attach evidence
                </p>
              </div>
            )}
          </div>
        )}

        {/* Audit tab */}
        {tab === 'audit' && (
          <div className={styles.auditSection}>
            <div className={styles.auditNotice}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{flexShrink:0}}>
                <rect x="3" y="11" width="18" height="11" rx="2" stroke="currentColor" strokeWidth="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              <span>
                <strong>ODEQ Security Notice</strong> — All classification overrides require
                an authorized inspector token. Actions are permanently logged.
              </span>
            </div>

            <form onSubmit={handleAudit} className={styles.auditForm}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Inspector Security Token PIN</label>
                <input
                  type="password" value={pin}
                  onChange={e => setPin(e.target.value)}
                  placeholder="PIN-XXXX"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Material Classification Override</label>
                <select value={decision} onChange={e => setDecision(e.target.value)} className={styles.formSelect}>
                  <option value="MANUALLY_CONFIRMED_LEAD">● Confirmed LEAD — Schedule Replacement</option>
                  <option value="MANUALLY_CONFIRMED_SAFE">✓ Confirmed SAFE — Non-Lead Material</option>
                </select>
              </div>
              {msg && (
                <div className={`${styles.msg} ${styles[`msg_${msg.type}`]}`}>{msg.text}</div>
              )}
              <button type="submit" disabled={loading || !pin} className={styles.submitBtn}>
                {loading ? 'Submitting…' : '🔒 Submit Field Verification'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}