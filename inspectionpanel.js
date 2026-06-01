// InspectionPanel.jsx — Record detail + audit form
import { useState } from 'react'
import styles from './InspectionPanel.module.css'

const PINS = { 'PIN-9402': 'A. Mutu (Badge #402)', 'PIN-1185': 'J. Doe (Badge #185)', 'PIN-2365': 'S. Smith (Badge #365)' }

function classify(record) {
  const s = record?.user_verified_status || ''
  if (s === 'MANUALLY_CONFIRMED_LEAD') return { label: 'LEAD',    color: 'red' }
  if (s === 'MANUALLY_CONFIRMED_SAFE') return { label: 'SAFE',    color: 'green' }
  const d = record?.ai_distance
  if (d !== null && d !== undefined && d < 0.35) return { label: 'SUSPECT', color: 'red' }
  if (d !== null && d !== undefined)              return { label: 'CLEAR',   color: 'green' }
  return { label: 'UNKNOWN', color: 'amber' }
}

function Attr({ label, value, mono, accent }) {
  return (
    <div className={styles.attr}>
      <span className={styles.attrLabel}>{label}</span>
      <span className={`${styles.attrValue} ${mono ? 'mono' : ''} ${accent ? styles.accent : ''}`}>{value ?? '—'}</span>
    </div>
  )
}

export default function InspectionPanel({ record, onClose }) {
  const [pin,      setPin]      = useState('')
  const [decision, setDecision] = useState('MANUALLY_CONFIRMED_SAFE')
  const [msg,      setMsg]      = useState(null)
  const [loading,  setLoading]  = useState(false)

  if (!record) return (
    <div className={styles.empty}>
      <div className={styles.emptyIcon}>🔬</div>
      <p>Select a record from the list or map to open the inspection workspace</p>
    </div>
  )

  const { label, color } = classify(record)
  const conf = record.ai_distance !== null && record.ai_distance !== undefined
    ? Math.min(99.9, Math.max(50, record.ai_distance < 0.35
        ? 99.9 - (record.ai_distance / 0.35) * 34.9
        : 65 + ((Math.min(record.ai_distance, 1) - 0.35) / 0.65) * 34.9
      )).toFixed(1)
    : null

  async function handleAudit(e) {
    e.preventDefault()
    if (!PINS[pin]) { setMsg({ type: 'error', text: 'Invalid security token.' }); return }
    setLoading(true)
    try {
      const res = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ evidence_id: record.evidence_id, status: decision, inspector_pin: pin })
      })
      const json = await res.json()
      if (res.ok) {
        setMsg({ type: 'success', text: json.message })
        setPin('')
      } else {
        setMsg({ type: 'error', text: json.detail || 'Server error' })
      }
    } catch {
      setMsg({ type: 'error', text: 'Network error — is the API running?' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={`${styles.chip} ${styles[`chip_${color}`]}`}>{label}</span>
          <span className={styles.recId}>EV-{record.evidence_id} · SL-{record.service_line_id}</span>
        </div>
        <button className={styles.closeBtn} onClick={onClose}>✕</button>
      </div>

      <div className={styles.body}>
        {/* Photo */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>📷 Field Photo</div>
          {record.photo_url && record.photo_url.startsWith('http') ? (
            <img src={record.photo_url} alt="Field photo" className={styles.photo} />
          ) : (
            <div className={styles.noPhoto}>No photo on record</div>
          )}
        </div>

        {/* AI Classification */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>🧠 PIPE_VISION_AI Classification</div>
          <div className={`${styles.classBar} ${styles[`classBar_${color}`]}`}>
            <span className={styles.classLabel}>{label} {conf ? `· ${conf}% confidence` : ''}</span>
            {record.ai_distance !== null && record.ai_distance !== undefined &&
              <span className={`${styles.distVal} mono`}>Cosine: {Number(record.ai_distance).toFixed(4)}</span>
            }
          </div>
        </div>

        {/* Attributes */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>📊 Record Attributes</div>
          <div className={styles.attrs}>
            <Attr label="Evidence ID"    value={`EV-${record.evidence_id}`} mono />
            <Attr label="Service Line"   value={`SL-${record.service_line_id}`} mono />
            <Attr label="GPS Latitude"   value={record.gps_latitude?.toFixed(6)} mono />
            <Attr label="GPS Longitude"  value={record.gps_longitude?.toFixed(6)} mono />
            <Attr label="Upload Date"    value={record.upload_date ? new Date(record.upload_date).toLocaleString() : '—'} />
            <Attr label="Audit Status"   value={record.user_verified_status?.replace('MANUALLY_CONFIRMED_','') || 'UNVERIFIED'} accent />
            <Attr label="Inspector"      value={record.audited_by || '—'} />
            <Attr label="Target Engine"  value="PIPE_VISION_AI · ResNet-50 v1-12" />
          </div>
        </div>

        {/* Audit form */}
        <div className={styles.section}>
          <div className={styles.sectionTitle}>🔒 Field Verification Sign-Off</div>
          <form onSubmit={handleAudit} className={styles.form}>
            <div className={styles.notice}>
              ODEQ Security Notice: All overrides require an authorized inspector token.
            </div>
            <label className={styles.formLabel}>Inspector Security Token PIN</label>
            <input
              type="password" value={pin} onChange={e => setPin(e.target.value)}
              placeholder="PIN-XXXX" className={styles.input}
            />
            <label className={styles.formLabel}>Material Classification</label>
            <select value={decision} onChange={e => setDecision(e.target.value)} className={styles.select}>
              <option value="MANUALLY_CONFIRMED_LEAD">✕ Confirmed LEAD — Schedule Replacement</option>
              <option value="MANUALLY_CONFIRMED_SAFE">✓ Confirmed SAFE — Non-Lead Material</option>
            </select>
            {msg && <div className={`${styles.msg} ${styles[`msg_${msg.type}`]}`}>{msg.text}</div>}
            <button type="submit" className={styles.submitBtn} disabled={loading || !pin}>
              {loading ? 'Submitting…' : 'Submit Field Verification'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}