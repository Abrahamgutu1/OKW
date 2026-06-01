// App.jsx — OKW FieldSync Enterprise Platform
import React, { useState } from 'react'
import { useData }      from './hooks/useData'
import Sidebar          from './components/Sidebar'
import Topbar           from './components/Topbar'
import AlertBanner      from './components/AlertBanner'
import KPICards         from './components/KPICards'
import DataTable        from './components/DataTable'
import MapPanel         from './components/MapPanel'
import DetailPanel      from './components/DetailPanel'
import styles           from './App.module.css'

function ReportsPage({ kpis }) {
  const [status,   setStatus]   = React.useState(null)
  const [loading,  setLoading]  = React.useState(false)
  const [pdfReady, setPdfReady] = React.useState(false)

  async function handleGenerate() {
    setLoading(true)
    setStatus(null)
    setPdfReady(false)
    try {
      const res = await fetch('/api/report', { method: 'POST' })
      if (res.ok) {
        const blob = await res.blob()
        const url  = window.URL.createObjectURL(blob)
        const a    = document.createElement('a')
        a.href     = url
        a.download = `OKW_ODEQ_Compliance_${new Date().toISOString().slice(0,10)}.pdf`
        a.click()
        window.URL.revokeObjectURL(url)
        setStatus({ type: 'success', text: 'Report compiled and downloaded successfully.' })
        setPdfReady(true)
      } else {
        const json = await res.json()
        setStatus({ type: 'error', text: json.detail || 'Compilation failed.' })
      }
    } catch (e) {
      setStatus({ type: 'error', text: 'Network error — is the API running?' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{height:'100%', overflowY:'auto', padding:20}}>
      <div style={{maxWidth:640}}>
        {/* Header card */}
        <div style={{
          background:'#fff', border:'1px solid var(--gray-200)',
          borderRadius:'var(--radius-lg)', boxShadow:'var(--shadow-sm)',
          overflow:'hidden', marginBottom:16
        }}>
          <div style={{
            background:'var(--brand-700)', padding:'20px 24px',
            borderBottom:'1px solid var(--gray-200)'
          }}>
            <div style={{fontSize:11, fontWeight:700, color:'rgba(255,255,255,0.6)',
              textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:6}}>
              COMPLIANCE · REPORTS
            </div>
            <h2 style={{fontSize:18, fontWeight:700, color:'#fff', margin:0}}>
              ODEQ Compliance Audit Report
            </h2>
            <p style={{fontSize:12, color:'rgba(255,255,255,0.7)', margin:'4px 0 0'}}>
              Oklahoma Lead & Copper Rule Revisions · 40 CFR §141 · PWSID OK1020401
            </p>
          </div>

          <div style={{padding:'20px 24px'}}>
            {/* Stats */}
            <div style={{
              display:'grid', gridTemplateColumns:'repeat(4,1fr)',
              gap:12, marginBottom:20
            }}>
              {[
                { label:'Records',  value: kpis?.total    ?? 0, color:'var(--brand-600)' },
                { label:'Flagged',  value: kpis?.suspect  ?? 0, color:'var(--danger-600)' },
                { label:'Verified', value: kpis?.verified ?? 0, color:'var(--success-600)' },
                { label:'Pending',  value: kpis?.pending  ?? 0, color:'var(--warn-600)' },
              ].map(s => (
                <div key={s.label} style={{
                  background:'var(--gray-50)', border:'1px solid var(--gray-200)',
                  borderRadius:'var(--radius-md)', padding:'12px 14px', textAlign:'center'
                }}>
                  <div style={{fontSize:24, fontWeight:700, fontFamily:'var(--font-mono)', color:s.color}}>
                    {s.value}
                  </div>
                  <div style={{fontSize:10, color:'var(--gray-500)', textTransform:'uppercase',
                    letterSpacing:'0.07em', marginTop:2}}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Info */}
            <div style={{
              background:'var(--gray-50)', border:'1px solid var(--gray-200)',
              borderRadius:'var(--radius-md)', padding:'12px 14px',
              marginBottom:20, fontSize:12, color:'var(--gray-600)', lineHeight:1.8
            }}>
              <strong style={{color:'var(--gray-800)'}}>What this generates:</strong> A legally binding
              LaTeX/PDF audit document including all evidence records, AI classification scores,
              inspector sign-offs, GPS coordinates, and a formal legal attestation section —
              formatted for official ODEQ LSLI submission.<br/>
              <span style={{color:'var(--warn-700)'}}>
                ⚠ Requires <code style={{background:'var(--gray-100)',padding:'1px 4px',borderRadius:3,
                fontFamily:'var(--font-mono)',fontSize:11}}>pdflatex</code> installed:
                <code style={{background:'var(--gray-100)',padding:'1px 4px',borderRadius:3,
                fontFamily:'var(--font-mono)',fontSize:11, marginLeft:6}}>brew install --cask mactex</code>
              </span>
            </div>

            {/* Status message */}
            {status && (
              <div style={{
                padding:'10px 14px', borderRadius:'var(--radius-md)',
                marginBottom:16, fontSize:12,
                background: status.type === 'success' ? 'var(--success-100)' : 'var(--danger-100)',
                color: status.type === 'success' ? 'var(--success-700)' : 'var(--danger-700)',
                border: `1px solid ${status.type === 'success' ? 'rgba(22,163,74,0.2)' : 'rgba(220,38,38,0.2)'}`
              }}>
                {status.type === 'success' ? '✅' : '❌'} {status.text}
              </div>
            )}

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={loading}
              style={{
                width:'100%', padding:'12px 20px',
                background: loading ? 'var(--gray-300)' : 'var(--brand-600)',
                color: loading ? 'var(--gray-500)' : '#fff',
                border:'none', borderRadius:'var(--radius-md)',
                fontSize:14, fontWeight:700, cursor: loading ? 'not-allowed' : 'pointer',
                fontFamily:'var(--font-ui)',
                boxShadow: loading ? 'none' : '0 2px 4px rgba(0,98,189,0.3)',
                transition:'all 0.15s', display:'flex', alignItems:'center',
                justifyContent:'center', gap:8
              }}
            >
              {loading ? (
                <>
                  <span style={{display:'inline-block',animation:'spin 1s linear infinite'}}>⟳</span>
                  Compiling LaTeX Report…
                </>
              ) : (
                <>📄 Generate & Download ODEQ Compliance Report</>
              )}
            </button>
            <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
          </div>
        </div>

        {/* Compliance framework card */}
        <div style={{
          background:'#fff', border:'1px solid var(--gray-200)',
          borderRadius:'var(--radius-lg)', boxShadow:'var(--shadow-sm)', padding:'16px 20px'
        }}>
          <div style={{fontSize:10, fontWeight:700, color:'var(--gray-500)',
            textTransform:'uppercase', letterSpacing:'0.1em', marginBottom:12}}>
            Regulatory Framework
          </div>
          {[
            ['Authority',        'Oklahoma Department of Environmental Quality (ODEQ)'],
            ['Federal Rule',     '40 CFR Part 141 — Lead & Copper Rule Revisions (LCRR/LCRI)'],
            ['State Code',       'Oklahoma Administrative Code 252:641'],
            ['PWSID',            'OK1020401'],
            ['1987 Lead Ban',    'Installations ≥1987 auto-classified NON-LEAD per Safe Drinking Water Act'],
            ['AI Engine',        'PIPE_VISION_AI · ResNet-50 v1-12 · Cosine Distance Threshold: 0.35'],
            ['Report Format',    'LaTeX typeset PDF · ISO A4 · Legally certifiable'],
          ].map(([label, value]) => (
            <div key={label} style={{
              display:'flex', justifyContent:'space-between', alignItems:'flex-start',
              padding:'8px 0', borderBottom:'1px solid var(--gray-100)', gap:16
            }}>
              <span style={{fontSize:11, color:'var(--gray-500)', fontWeight:600,
                textTransform:'uppercase', letterSpacing:'0.05em', flexShrink:0, width:140}}>{label}</span>
              <span style={{fontSize:11, color:'var(--gray-700)', textAlign:'right',
                fontFamily:'var(--font-mono)'}}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const { data, loading, error, refresh, lastRefresh } = useData()
  const [page,     setPage]     = useState('dashboard')
  const [selected, setSelected] = useState(null)

  const records   = data?.records || []
  const kpis      = data?.kpis
  const connected = !!data && !error

  const suspects = records.filter(r =>
    r.ai_distance !== null && r.ai_distance < 0.35 && r.user_verified_status === 'UNVERIFIED'
  ).length

  function handleSelect(rec) {
    setSelected(rec)
    if (page !== 'inventory') setPage('inventory')
  }

  return (
    <div className={styles.shell}>
      {/* ── Sidebar ── */}
      <Sidebar activePage={page} onNavigate={p => { setPage(p); if (p !== 'inventory') setSelected(null) }} />

      {/* ── Main area ── */}
      <div className={styles.main}>
        <Topbar
          page={page}
          connected={connected}
          lastRefresh={lastRefresh}
          onRefresh={refresh}
          alertCount={suspects}
        />

        {/* Alert banner */}
        <AlertBanner records={records} />

        {/* Connection error */}
        {error && !loading && (
          <div className={styles.errorStrip}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 8v4m0 4h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>
              Cannot reach API — ensure <code>uvicorn main:app --port 8000</code> is running and Oracle is up.
            </span>
            <button className={styles.retryBtn} onClick={refresh}>Retry connection</button>
          </div>
        )}

        {/* ── Page content ── */}
        <div className={styles.content}>

          {/* DASHBOARD */}
          {page === 'dashboard' && (
            <div className={styles.dashLayout}>
              <div className={styles.dashHeader}>
                <div>
                  <h2 className={styles.dashTitle}>Lead Service Line Inventory Overview</h2>
                  <p className={styles.dashSub}>
                    Oklahoma City Public Works · ODEQ LCRR/LCRI Compliance · PWSID OK1020401
                  </p>
                </div>
                <div className={styles.dashActions}>
                  <button className={styles.btnSecondary} onClick={() => setPage('inventory')}>
                    View Inventory →
                  </button>
                  <button className={styles.btnPrimary} onClick={() => setPage('map')}>
                    Open Map
                  </button>
                </div>
              </div>

              <KPICards kpis={kpis} />

              <div className={styles.dashGrid}>
                {/* Recent records */}
                <div className={styles.dashCard}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardTitle}>Recent Evidence Records</span>
                    <button className={styles.cardAction} onClick={() => setPage('inventory')}>View all →</button>
                  </div>
                  <table className={styles.miniTable}>
                    <thead>
                      <tr>
                        <th>EV</th><th>SL</th><th>Status</th><th>AI Score</th><th>Inspector</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.slice(0,6).map(rec => {
                        const d = rec.ai_distance
                        const isLead = d !== null && d !== undefined && d < 0.35
                        const isVerified = rec.user_verified_status?.includes('CONFIRMED')
                        return (
                          <tr key={rec.evidence_id} onClick={() => handleSelect(rec)} className={styles.miniRow}>
                            <td className="mono">EV-{rec.evidence_id}</td>
                            <td className="mono">SL-{rec.service_line_id}</td>
                            <td>
                              <span className={`badge ${isVerified ? 'badge-success' : isLead ? 'badge-danger' : 'badge-neutral'}`}>
                                {isVerified ? '✓ Verified' : isLead ? '⚠ Suspect' : '○ Clear'}
                              </span>
                            </td>
                            <td className="mono" style={{color: isLead ? 'var(--danger-600)' : 'var(--success-600)', fontWeight:600}}>
                              {d !== null && d !== undefined ? Number(d).toFixed(4) : 'N/A'}
                            </td>
                            <td style={{color:'var(--gray-500)', fontSize:11}}>{rec.audited_by || '—'}</td>
                          </tr>
                        )
                      })}
                      {records.length === 0 &&
                        <tr><td colSpan={5} style={{textAlign:'center', color:'var(--gray-400)', padding:20, fontSize:12}}>
                          {loading ? 'Loading…' : 'No records — check database connection'}
                        </td></tr>
                      }
                    </tbody>
                  </table>
                </div>

                {/* Compliance summary */}
                <div className={styles.dashCard}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardTitle}>Compliance Summary</span>
                    <span className={styles.cardBadge}>LCRR 2026</span>
                  </div>
                  <div className={styles.complianceRows}>
                    {[
                      { label: 'Total Service Lines',    value: kpis?.lines,    color: 'var(--brand-600)' },
                      { label: 'Lead Suspect (AI)',       value: kpis?.suspect,  color: 'var(--danger-600)' },
                      { label: 'Inspector Verified',      value: kpis?.verified, color: 'var(--success-600)' },
                      { label: 'Pending Review',          value: kpis?.pending,  color: 'var(--warn-600)' },
                      { label: 'Photo Evidence on Record',value: kpis?.has_photo,color: 'var(--teal-600)' },
                    ].map(row => (
                      <div key={row.label} className={styles.compRow}>
                        <span className={styles.compLabel}>{row.label}</span>
                        <div className={styles.compRight}>
                          <div className={styles.compBar}>
                            <div style={{
                              width: `${kpis?.total ? Math.min((row.value/kpis.total)*100,100) : 0}%`,
                              background: row.color, height:'100%', borderRadius:2, transition:'width 0.4s'
                            }}/>
                          </div>
                          <span className={styles.compVal} style={{color: row.color}}>{row.value ?? '—'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className={styles.complianceFoot}>
                    <span>Authority: Oklahoma DEQ</span>
                    <span>Framework: 40 CFR §141</span>
                    <span>PWSID: OK1020401</span>
                  </div>
                </div>

                {/* Mini map */}
                <div className={styles.dashCard} style={{gridColumn:'1/-1', height:320}}>
                  <div className={styles.cardHeader}>
                    <span className={styles.cardTitle}>Service Line Field Locations</span>
                    <button className={styles.cardAction} onClick={() => setPage('map')}>Full map →</button>
                  </div>
                  <div style={{flex:1, minHeight:0}}>
                    <MapPanel records={records} selectedId={selected?.evidence_id} onSelect={handleSelect} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* INVENTORY */}
          {page === 'inventory' && (
            <div className={styles.inventoryLayout}>
              <div className={styles.inventoryTable}>
                <DataTable records={records} onSelect={handleSelect} selectedId={selected?.evidence_id} />
              </div>
              {selected && (
                <div className={styles.inventoryPanel}>
                  <DetailPanel record={selected} onClose={() => setSelected(null)} />
                </div>
              )}
            </div>
          )}

          {/* MAP */}
          {page === 'map' && (
            <div className={styles.mapPage}>
              <MapPanel records={records} selectedId={selected?.evidence_id} onSelect={handleSelect} />
            </div>
          )}

          {/* INSPECTIONS */}
          {page === 'inspection' && (
            <div className={styles.inspectionPage}>
              <div className={styles.inspectionList}>
                <DataTable
                  records={records.filter(r => r.ai_distance !== null && r.ai_distance < 0.35)}
                  onSelect={handleSelect}
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

          {/* REPORTS */}
          {page === 'reports' && (
            <ReportsPage kpis={kpis} />
          )}

          {/* SETTINGS */}
          {page === 'settings' && (
            <div className={styles.settingsPage}>
              <div className={styles.settingsCard}>
                <h3 className={styles.settingsTitle}>⚙ System Configuration</h3>
                <div className={styles.settingsList}>
                  {[
                    { label: 'Oracle Database',  value: 'localhost:1521/FREEPDB1', type: 'connection' },
                    { label: 'API Backend',       value: 'localhost:8000',         type: 'connection' },
                    { label: 'PWSID',             value: 'OK1020401',              type: 'info' },
                    { label: 'AI Engine',         value: 'PIPE_VISION_AI ResNet-50 v1-12', type: 'info' },
                    { label: 'Vector Threshold',  value: '< 0.35 (Lead Suspect)',  type: 'info' },
                    { label: 'Regulatory',        value: 'ODEQ LCRR/LCRI · 40 CFR §141', type: 'info' },
                  ].map(s => (
                    <div key={s.label} className={styles.settingRow}>
                      <span className={styles.settingLabel}>{s.label}</span>
                      <span className={`${styles.settingValue} mono`}>{s.value}</span>
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
          <span style={{color:'var(--teal-600)'}}>
            {data?.vec_ok ? '⬡ VECTOR_DISTANCE Active' : '◇ Standard Query'}
          </span>
        </div>
      </div>
    </div>
  )
}