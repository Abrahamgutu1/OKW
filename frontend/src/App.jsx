// App.jsx — OKW FieldSync · ArcGIS/Palantir/Fulcrum Dark Ops
import React, { useState, useEffect } from 'react'
import { useData }    from './hooks/useData'
import Sidebar        from './components/Sidebar'
import Topbar         from './components/Topbar'
import AlertBanner    from './components/AlertBanner'
import DataTable      from './components/DataTable'
import MapPanel       from './components/MapPanel'
import DetailPanel    from './components/DetailPanel'
import styles         from './App.module.css'

// ── Animated counter ──────────────────────────────────────────────────────────
function AnimatedNum({ value, color }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    if (value == null) return
    const target = Number(value)
    const duration = 600
    const steps = 20
    const step = target / steps
    let current = 0
    let count = 0
    const timer = setInterval(() => {
      count++
      current = Math.min(Math.round(step * count), target)
      setDisplay(current)
      if (count >= steps) clearInterval(timer)
    }, duration / steps)
    return () => clearInterval(timer)
  }, [value])
  return <span style={{ color }}>{display ?? '—'}</span>
}

// ── Deadline countdown ────────────────────────────────────────────────────────
function DeadlineCountdown() {
  const deadline = new Date('2027-11-01')
  const now = new Date()
  const days = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24))
  const urgency = days < 90 ? '#f85149' : days < 180 ? '#e3b341' : '#8b949e'
  return (
    <div className={styles.deadlinePill} style={{ borderColor: `${urgency}33`, color: urgency }}>
      <div className={styles.deadlineDot} style={{ background: urgency }} />
      {days}d to LCRI deadline · Nov 1 2027
    </div>
  )
}

// ── Reports page ──────────────────────────────────────────────────────────────
function ReportsPage({ kpis }) {
  const [status,  setStatus]  = React.useState(null)
  const [loading, setLoading] = React.useState(false)
  const [step,    setStep]    = React.useState(null)

  const STEPS = ['Querying Oracle', 'Compiling Assets', 'Validating Layout', 'Typesetting LaTeX', 'Ready']

  async function handleGenerate() {
    setLoading(true); setStatus(null)
    for (let i = 0; i < STEPS.length - 1; i++) {
      setStep(STEPS[i])
      await new Promise(r => setTimeout(r, 400))
    }
    try {
      const res = await fetch('/api/report', { method: 'POST' })
      if (res.ok) {
        const blob = await res.blob()
        const url  = window.URL.createObjectURL(blob)
        const a    = document.createElement('a')
        a.href = url; a.download = `OKW_ODEQ_${new Date().toISOString().slice(0,10)}.pdf`
        a.click(); window.URL.revokeObjectURL(url)
        setStep('Ready')
        setStatus({ type: 'success', text: 'Report compiled and downloaded.' })
      } else {
        const j = await res.json()
        setStatus({ type: 'error', text: j.detail || 'Compilation failed.' })
      }
    } catch {
      setStatus({ type: 'error', text: 'Network error — is the API running?' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 20 }}>
      <div style={{ maxWidth: 560 }}>
        {/* Header */}
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)', overflow: 'hidden', marginBottom: 12
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #004A8F 0%, #0062BD 100%)',
            padding: '14px 18px', borderBottom: '1px solid rgba(255,255,255,0.08)'
          }}>
            <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 4 }}>
              COMPLIANCE · ODEQ SUBMISSION
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#fff' }}>Lead Service Line Inventory Audit Report</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)', marginTop: 3 }}>
              40 CFR §141.84 · Oklahoma DEQ · PWSID OK1020401
            </div>
          </div>

          <div style={{ padding: '14px 18px' }}>
            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 16 }}>
              {[
                { label: 'Records',  value: kpis?.total    ?? 0, color: 'var(--brand-400)' },
                { label: 'Flagged',  value: kpis?.suspect  ?? 0, color: 'var(--danger)' },
                { label: 'Verified', value: kpis?.verified ?? 0, color: 'var(--success)' },
                { label: 'Pending',  value: kpis?.pending  ?? 0, color: 'var(--warn)' },
              ].map(s => (
                <div key={s.label} style={{
                  background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)', padding: '8px 10px', textAlign: 'center'
                }}>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'var(--font-mono)', color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Progress steps */}
            {loading && (
              <div style={{ marginBottom: 14 }}>
                {STEPS.map((s, i) => {
                  const done    = STEPS.indexOf(step) > i
                  const current = step === s
                  return (
                    <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
                      <div style={{
                        width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                        background: done ? 'var(--success)' : current ? 'var(--brand-500)' : 'var(--bg-overlay)',
                        border: `1px solid ${done ? 'var(--success)' : current ? 'var(--brand-400)' : 'var(--border-subtle)'}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 8, color: '#fff'
                      }}>
                        {done ? '✓' : current ? '●' : ''}
                      </div>
                      <span style={{
                        fontSize: 11, fontFamily: 'var(--font-mono)',
                        color: done ? 'var(--success)' : current ? 'var(--text-primary)' : 'var(--text-muted)'
                      }}>{s}</span>
                    </div>
                  )
                })}
              </div>
            )}

            {status && (
              <div style={{
                padding: '8px 12px', borderRadius: 'var(--radius-md)', marginBottom: 12,
                fontSize: 11, fontFamily: 'var(--font-mono)',
                background: status.type === 'success' ? 'var(--success-dim)' : 'var(--danger-dim)',
                color: status.type === 'success' ? 'var(--success)' : 'var(--danger)',
                border: `1px solid ${status.type === 'success' ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`
              }}>
                {status.type === 'success' ? '✓' : '✗'} {status.text}
              </div>
            )}

            <button onClick={handleGenerate} disabled={loading} style={{
              width: '100%', padding: '10px 16px',
              background: loading ? 'var(--bg-overlay)' : 'var(--brand-500)',
              color: loading ? 'var(--text-muted)' : '#fff',
              border: '1px solid ' + (loading ? 'var(--border-subtle)' : 'transparent'),
              borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-ui)',
              transition: 'all 0.15s'
            }}>
              {loading ? `${step}…` : '↓ Generate ODEQ Compliance Report (PDF)'}
            </button>

            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, fontFamily: 'var(--font-mono)' }}>
              Requires pdflatex · <code style={{ color: 'var(--teal)' }}>brew install --cask mactex</code>
            </div>
          </div>
        </div>

        {/* Regulatory table */}
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)', overflow: 'hidden'
        }}>
          <div style={{ padding: '8px 14px', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
            <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              REGULATORY FRAMEWORK
            </span>
          </div>
          {[
            ['Authority',     'Oklahoma Department of Environmental Quality (ODEQ)'],
            ['Federal Rule',  '40 CFR Part 141 — LCRR/LCRI'],
            ['State Code',    'Oklahoma Administrative Code 252:641'],
            ['PWSID',         'OK1020401'],
            ['AI Engine',     'PIPE_VISION_AI · ResNet-50 · Cosine ≤ 0.35'],
            ['Format',        'LaTeX PDF · ISO A4 · Legally certifiable'],
          ].map(([l, v]) => (
            <div key={l} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '7px 14px', borderBottom: '1px solid var(--border-subtle)'
            }}>
              <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', width: 120, flexShrink: 0 }}>{l}</span>
              <span style={{ fontSize: 10, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', textAlign: 'right' }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const { data, loading, error, refresh, lastRefresh } = useData()
  const [page,     setPage]     = useState('dashboard')
  const [selected, setSelected] = useState(null)
  const [mapBounds, setMapBounds] = useState(null)

  const records   = data?.records || []
  const kpis      = data?.kpis
  const connected = !!data && !error

  // Filter records by current map bounds (ArcGIS bidirectional filtering)
  const visibleRecords = mapBounds
    ? records.filter(r =>
        r.gps_latitude  >= mapBounds.south &&
        r.gps_latitude  <= mapBounds.north &&
        r.gps_longitude >= mapBounds.west  &&
        r.gps_longitude <= mapBounds.east
      )
    : records

  const suspects = records.filter(r =>
    r.ai_distance !== null && r.ai_distance < 0.35 && r.user_verified_status === 'UNVERIFIED'
  ).length

  function handleSelect(rec) {
    setSelected(rec)
    if (page !== 'inventory') setPage('inventory')
  }

  function handleMapSelect(rec) {
    setSelected(rec)
  }

  return (
    <div className={styles.shell}>
      <Sidebar activePage={page} onNavigate={p => { setPage(p); if (p !== 'inventory') setSelected(null) }} />

      <div className={styles.main}>
        <AlertBanner records={records} />

        {error && !loading && (
          <div className={styles.errorStrip}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 8v4m0 4h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Cannot reach API — ensure <code>uvicorn main:app --port 8000</code> is running and Oracle is up.
            <button className={styles.retryBtn} onClick={refresh}>Retry connection</button>
          </div>
        )}

        <div className={styles.content}>

          {/* ── DASHBOARD ── ArcGIS operational layout */}
          {page === 'dashboard' && (
            <div className={styles.dashLayout}>

              {/* Header row */}
              <div className={styles.dashHeader}>
                <div className={styles.dashTitleBlock}>
                  <div className={styles.dashTitle}>Lead Service Line Inventory — Operational View</div>
                  <div className={styles.dashSub}>Oklahoma City Public Works · ODEQ LCRR/LCRI · PWSID OK1020401</div>
                </div>
                <div className={styles.dashActions}>
                  <DeadlineCountdown />
                  <button className={styles.btnSecondary} onClick={() => setPage('inventory')}>Inventory →</button>
                  <button className={styles.btnPrimary} onClick={() => setPage('reports')}>Generate Report</button>
                </div>
              </div>

              {/* KPI strip */}
              <div className={styles.kpiStrip}>
                {[
                  { label: 'Total Records',      value: kpis?.total,     sub: `${kpis?.lines ?? 0} service lines`, color: 'kpiBlue'  },
                  { label: 'Lead Suspect',        value: kpis?.suspect,   sub: 'AI distance < 0.35',                color: 'kpiRed'   },
                  { label: 'Inspector Verified',  value: kpis?.verified,  sub: 'Signed off on record',              color: 'kpiGreen' },
                  { label: 'Pending Review',      value: kpis?.pending,   sub: 'Awaiting field inspection',         color: 'kpiAmber' },
                  { label: 'Photo Evidence',      value: kpis?.has_photo, sub: 'Images on record',                  color: 'kpiTeal'  },
                  {
                    label: 'Inventory Progress',
                    value: kpis?.total ? `${Math.round((kpis.verified / kpis.total) * 100)}%` : '0%',
                    sub: 'of total classified',
                    color: 'kpiGreen'
                  },
                ].map(k => (
                  <div key={k.label} className={`${styles.kpiItem} ${styles[k.color]}`}>
                    <div className={styles.kpiLabel}>{k.label}</div>
                    <div className={styles.kpiValue}>{k.value ?? '—'}</div>
                    <div className={styles.kpiSub}>{k.sub}</div>
                  </div>
                ))}
              </div>

              {/* Map — left, full height */}
              <div className={styles.dashBody}>
                <div className={styles.dashMap}>
                  <MapPanel
                    records={records}
                    selectedId={selected?.evidence_id}
                    onSelect={handleMapSelect}
                    onBoundsChange={setMapBounds}
                  />
                </div>
              </div>

              {/* Right panel — records + compliance */}
              <div className={styles.dashRight}>
                <div className={styles.rightPanel}>
                  <div className={styles.rightPanelHeader}>
                    <span className={styles.rightPanelTitle}>
                      {mapBounds ? `${visibleRecords.length} in view` : 'Recent Records'}
                    </span>
                    <button className={styles.rightPanelAction} onClick={() => setPage('inventory')}>View all →</button>
                  </div>
                  <div className={styles.recordFeed}>
                    {(mapBounds ? visibleRecords : records).slice(0, 30).map(rec => {
                      const d = rec.ai_distance
                      const isLead = d !== null && d !== undefined && d < 0.35
                      const isVerified = rec.user_verified_status?.includes('CONFIRMED')
                      const scoreColor = isLead ? 'var(--danger)' : 'var(--success)'
                      return (
                        <div
                          key={rec.evidence_id}
                          className={`${styles.feedRow} ${selected?.evidence_id === rec.evidence_id ? styles.feedSelected : ''}`}
                          onClick={() => setSelected(rec)}
                        >
                          <span className={styles.feedRowId}>EV-{rec.evidence_id}</span>
                          <span className={styles.feedRowStatus}>
                            <span className={`badge ${isVerified ? 'badge-success' : isLead ? 'badge-danger' : 'badge-neutral'}`}>
                              {isVerified ? '✓ Verified' : isLead ? '⚠ Suspect' : '○ Clear'}
                            </span>
                          </span>
                          <span className={styles.feedRowScore} style={{ color: scoreColor }}>
                            {d !== null && d !== undefined ? Number(d).toFixed(3) : 'N/A'}
                          </span>
                        </div>
                      )
                    })}
                    {records.length === 0 && (
                      <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 11 }}>
                        {loading ? 'Loading…' : 'No records'}
                      </div>
                    )}
                  </div>

                  {/* Compliance mini bars */}
                  <div className={styles.compliancePanel}>
                    <div className={styles.compPanelTitle}>Compliance Summary</div>
                    {[
                      { label: 'Lead Suspect',  value: kpis?.suspect,  total: kpis?.total, color: 'var(--danger)' },
                      { label: 'Verified',      value: kpis?.verified, total: kpis?.total, color: 'var(--success)' },
                      { label: 'Pending',       value: kpis?.pending,  total: kpis?.total, color: 'var(--warn)' },
                      { label: 'Photo Evidence',value: kpis?.has_photo,total: kpis?.total, color: 'var(--teal)' },
                    ].map(r => (
                      <div key={r.label} className={styles.compRow}>
                        <span className={styles.compRowLabel}>{r.label}</span>
                        <div className={styles.compRowBar}>
                          <div className={styles.compRowFill} style={{
                            width: `${r.total ? Math.min((r.value / r.total) * 100, 100) : 0}%`,
                            background: r.color
                          }} />
                        </div>
                        <span className={styles.compRowVal} style={{ color: r.color }}>{r.value ?? '—'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* ── INVENTORY — Fulcrum slide-out drawer ── */}
          {page === 'inventory' && (
            <div className={styles.inventoryLayout}>
              <div className={styles.inventoryTable}>
                <DataTable records={records} onSelect={setSelected} selectedId={selected?.evidence_id} />
              </div>
              {selected && (
                <div className={styles.inventoryPanel}>
                  <DetailPanel record={selected} onClose={() => setSelected(null)} />
                </div>
              )}
            </div>
          )}

          {/* ── MAP ── */}
          {page === 'map' && (
            <div style={{height:'100%', width:'100%', display:'flex', flexDirection:'column', overflow:'hidden'}}>
              <MapPanel
                records={records}
                selectedId={selected?.evidence_id}
                onSelect={handleMapSelect}
                onBoundsChange={setMapBounds}
              />
            </div>
          )}

          {/* ── INSPECTIONS ── */}
          {page === 'inspection' && (
            <div className={styles.inspectionPage}>
              <div className={styles.inspectionList}>
                <DataTable
                  records={records.filter(r => r.ai_distance !== null && r.ai_distance < 0.35)}
                  onSelect={setSelected}
                  selectedId={selected?.evidence_id}
                />
              </div>
              {selected && (
                <div className={styles.inspectionDetail}>
                  <DetailPanel record={selected} onClose={() => setSelected(null)} />
                </div>
              )}
            </div>
          )}

          {/* ── REPORTS ── */}
          {page === 'reports' && <ReportsPage kpis={kpis} />}

          {/* ── SETTINGS ── */}
          {page === 'settings' && (
            <div className={styles.settingsPage}>

              <div className={styles.settingsSection}>
                <div className={styles.settingsSectionTitle}>System Status</div>
                <div className={styles.statusGrid}>
                  {[
                    { label: 'API Backend',    value: 'Online',    sub: 'localhost:8000' },
                    { label: 'Oracle 23ai',    value: 'Connected', sub: 'FREEPDB1' },
                    { label: 'PIPE_VISION_AI', value: 'Loaded',    sub: 'YOLOv11n v2' },
                    { label: 'Gemini 2.5',     value: 'Active',    sub: 'Vision API' },
                  ].map(s => (
                    <div key={s.label} className={styles.statusCard}>
                      <div className={styles.statusCardTop}>
                        <span className={styles.statusDotOk} />
                        <span className={styles.statusLabel}>{s.label}</span>
                      </div>
                      <div className={styles.statusValue}>{s.value}</div>
                      <div className={styles.statusSub}>{s.sub}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.settingsSection}>
                <div className={styles.settingsSectionTitle}>Compliance Configuration</div>
                <div className={styles.settingsCard}>
                  {[
                    { label: 'PWSID',         value: 'OK1020401' },
                    { label: 'Utility',       value: 'Oklahoma City Public Works' },
                    { label: 'Regulatory',    value: 'ODEQ LCRR/LCRI · 40 CFR §141' },
                    { label: 'LCRI Deadline', value: 'November 1, 2027' },
                    { label: 'State Agency',  value: 'Oklahoma DEQ (ODEQ)' },
                  ].map(s => (
                    <div key={s.label} className={styles.settingRow}>
                      <span className={styles.settingLabel}>{s.label}</span>
                      <span className={styles.settingValue + ' mono'}>{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.settingsSection}>
                <div className={styles.settingsSectionTitle}>AI Engine</div>
                <div className={styles.settingsCard}>
                  {[
                    { label: 'Material Detection', value: 'Gemini 2.5 Flash' },
                    { label: 'Condition Model',    value: 'PIPE_VISION_AI YOLOv11n v2' },
                    { label: 'Training Images',    value: '31,013 augmented' },
                    { label: 'Corrosion Accuracy', value: '84.9% mAP50' },
                    { label: 'Vector Threshold',   value: '< 0.35 Lead Suspect' },
                  ].map(s => (
                    <div key={s.label} className={styles.settingRow}>
                      <span className={styles.settingLabel}>{s.label}</span>
                      <span className={styles.settingValue + ' mono'}>{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.settingsSection}>
                <div className={styles.settingsSectionTitle}>Inspector Security Tokens</div>
                <div className={styles.settingsCard}>
                  {[
                    { label: 'A. Mutu (Badge 402)',  value: 'PIN-9402' },
                    { label: 'J. Doe (Badge 185)',   value: 'PIN-1185' },
                    { label: 'S. Smith (Badge 365)', value: 'PIN-2365' },
                  ].map(s => (
                    <div key={s.label} className={styles.settingRow}>
                      <span className={styles.settingLabel}>{s.label}</span>
                      <span className={styles.settingValue + ' mono'} style={{background:'var(--bg-elevated)',padding:'2px 8px',borderRadius:4}}>{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.settingsSection}>
                <div className={styles.settingsSectionTitle}>About</div>
                <div className={styles.settingsCard}>
                  {[
                    { label: 'Product',   value: 'OKW FieldSync v2.0' },
                    { label: 'Stack',     value: 'SwiftUI · FastAPI · Oracle 23ai · React' },
                    { label: 'GitHub',    value: 'github.com/Abrahamgutu1/OKW' },
                    { label: 'Developer', value: 'Abraham Gutu · OU CS 2027' },
                  ].map(s => (
                    <div key={s.label} className={styles.settingRow}>
                      <span className={styles.settingLabel}>{s.label}</span>
                      <span className={styles.settingValue + ' mono'}>{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <span>OKW FieldSync v2.0 · Oracle 23ai · PWSID OK1020401 · ODEQ 2026</span>
          <span className={styles.footerLive}>
            <span className={styles.footerDot} />
            {data?.vec_ok ? 'VECTOR_DISTANCE Active' : 'Standard Query'}
          </span>
        </div>
      </div>
    </div>
  )
}
