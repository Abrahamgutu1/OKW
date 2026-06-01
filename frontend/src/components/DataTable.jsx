// DataTable.jsx — Enterprise sortable data table
import { useState, useMemo } from 'react'
import styles from './DataTable.module.css'

function StatusBadge({ record }) {
  const s = record.user_verified_status || ''
  const d = record.ai_distance
  if (s === 'MANUALLY_CONFIRMED_LEAD') return <span className="badge badge-danger">● Confirmed Lead</span>
  if (s === 'MANUALLY_CONFIRMED_SAFE') return <span className="badge badge-success">✓ Confirmed Safe</span>
  if (d !== null && d !== undefined && d < 0.35) return <span className="badge badge-danger">⚠ Lead Suspect</span>
  if (d !== null && d !== undefined) return <span className="badge badge-success">✓ Clear</span>
  return <span className="badge badge-neutral">— Unknown</span>
}

function AiScore({ value }) {
  if (value === null || value === undefined) return <span className={styles.na}>N/A</span>
  const d = Number(value)
  const color = d < 0.35 ? 'var(--danger-600)' : 'var(--success-600)'
  return (
    <div className={styles.scoreCell}>
      <span className={styles.scoreVal} style={{ color }}>{d.toFixed(4)}</span>
      <div className={styles.scoreBar}>
        <div
          className={styles.scoreFill}
          style={{ width: `${Math.min(d * 100, 100)}%`, background: color }}
        />
      </div>
    </div>
  )
}

const COLS = [
  { key: 'evidence_id',          label: 'EV ID',     width: 80,  mono: true },
  { key: 'service_line_id',      label: 'SL ID',     width: 80,  mono: true },
  { key: 'status',               label: 'Status',    width: 160, render: r => <StatusBadge record={r} /> },
  { key: 'ai_distance',          label: 'AI Score',  width: 140, render: r => <AiScore value={r.ai_distance} /> },
  { key: 'gps_latitude',         label: 'Latitude',  width: 110, mono: true, fmt: v => v?.toFixed(6) },
  { key: 'gps_longitude',        label: 'Longitude', width: 110, mono: true, fmt: v => v?.toFixed(6) },
  { key: 'upload_date',          label: 'Date',      width: 130, fmt: v => v ? new Date(v).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'2-digit'}) : '—' },
  { key: 'audited_by',           label: 'Inspector', width: 150, fmt: v => v || '—' },
]

export default function DataTable({ records, onSelect, selectedId }) {
  const [sortKey,  setSortKey]  = useState('evidence_id')
  const [sortDir,  setSortDir]  = useState('asc')
  const [filter,   setFilter]   = useState('all')
  const [search,   setSearch]   = useState('')
  const [selected, setSelected] = useState(new Set())

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
  }

  const filtered = useMemo(() => {
    let rows = records || []

    if (filter === 'suspect') rows = rows.filter(r => r.ai_distance !== null && r.ai_distance < 0.35)
    if (filter === 'verified') rows = rows.filter(r => r.user_verified_status?.includes('CONFIRMED'))
    if (filter === 'unverified') rows = rows.filter(r => r.user_verified_status === 'UNVERIFIED')

    if (search.trim()) {
      const q = search.toLowerCase()
      rows = rows.filter(r =>
        String(r.evidence_id).includes(q) ||
        String(r.service_line_id).includes(q) ||
        String(r.audited_by || '').toLowerCase().includes(q)
      )
    }

    return [...rows].sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey]
      if (av === null || av === undefined) return 1
      if (bv === null || bv === undefined) return -1
      if (typeof av === 'string') av = av.toLowerCase()
      if (typeof bv === 'string') bv = bv.toLowerCase()
      return sortDir === 'asc' ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1)
    })
  }, [records, filter, search, sortKey, sortDir])

  function toggleRow(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className={styles.wrapper}>
      {/* Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.filters}>
          {[
            { key: 'all',      label: 'All Records' },
            { key: 'suspect',  label: 'Lead Suspect' },
            { key: 'verified', label: 'Verified' },
            { key: 'unverified', label: 'Unverified' },
          ].map(f => (
            <button
              key={f.key}
              className={`${styles.filterBtn} ${filter === f.key ? styles.filterActive : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
              {f.key === 'suspect' && records &&
                <span className={styles.filterCount}>
                  {records.filter(r => r.ai_distance !== null && r.ai_distance < 0.35).length}
                </span>
              }
            </button>
          ))}
        </div>
        <div className={styles.toolbarRight}>
          <div className={styles.tableSearch}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2"/>
              <path d="m16.5 16.5 4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Filter table…"
              className={styles.tableSearchInput}
            />
          </div>
          <span className={styles.rowCount}>{filtered.length} records</span>
        </div>
      </div>

      {/* Table */}
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.checkCol}>
                <input type="checkbox" className={styles.check} />
              </th>
              {COLS.map(col => (
                <th
                  key={col.key}
                  className={`${styles.th} ${sortKey === col.key ? styles.thSorted : ''}`}
                  style={{ minWidth: col.width }}
                  onClick={() => toggleSort(col.key)}
                >
                  <div className={styles.thInner}>
                    {col.label}
                    <span className={styles.sortIcon}>
                      {sortKey === col.key ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
                    </span>
                  </div>
                </th>
              ))}
              <th className={styles.th} style={{ minWidth: 80 }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={COLS.length + 2} className={styles.emptyRow}>
                  No records match the current filter
                </td>
              </tr>
            )}
            {filtered.map(rec => {
              const isSelected = selectedId === rec.evidence_id
              const isChecked  = selected.has(rec.evidence_id)
              return (
                <tr
                  key={rec.evidence_id}
                  className={`${styles.tr} ${isSelected ? styles.trSelected : ''} ${isChecked ? styles.trChecked : ''}`}
                  onClick={() => onSelect(rec)}
                >
                  <td className={styles.checkCol} onClick={e => { e.stopPropagation(); toggleRow(rec.evidence_id) }}>
                    <input type="checkbox" className={styles.check} checked={isChecked} readOnly />
                  </td>
                  {COLS.map(col => (
                    <td key={col.key} className={`${styles.td} ${col.mono ? styles.tdMono : ''}`}>
                      {col.render
                        ? col.render(rec)
                        : col.fmt
                          ? col.fmt(rec[col.key])
                          : rec[col.key] ?? '—'
                      }
                    </td>
                  ))}
                  <td className={styles.td}>
                    <button className={styles.inspectBtn} onClick={e => { e.stopPropagation(); onSelect(rec) }}>
                      Inspect →
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination placeholder */}
      <div className={styles.pagination}>
        <span className={styles.paginationInfo}>
          Showing {filtered.length} of {records?.length ?? 0} records
        </span>
        <div className={styles.paginationBtns}>
          <button className={styles.pgBtn} disabled>← Previous</button>
          <span className={styles.pgCurrent}>Page 1</span>
          <button className={styles.pgBtn} disabled>Next →</button>
        </div>
      </div>
    </div>
  )
}