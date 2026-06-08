// MapPanel.jsx — ArcGIS-style map with bidirectional spatial filtering
import { useEffect, useRef, useState, useCallback } from 'react'
import styles from './MapPanel.module.css'

export default function MapPanel({ records, selectedId, onSelect, onBoundsChange }) {
  const mapRef      = useRef(null)
  const instanceRef = useRef(null)
  const markersRef  = useRef({})
  const [layer, setLayer] = useState('satellite')
  const tileLayers  = useRef({})

  // Force map to fill container when it becomes visible
  useEffect(() => {
    if (instanceRef.current || !mapRef.current) return
    import('leaflet').then(L => {
      const map = L.map(mapRef.current, {
        center: [35.22, -97.44], zoom: 13, zoomControl: false
      })

      const tiles = {
        street: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '©OpenStreetMap ©CartoDB', maxZoom: 19
        }),
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
          attribution: '©Esri', maxZoom: 19, maxNativeZoom: 18
        }),
        hybrid: L.layerGroup([
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '©Esri', maxZoom: 19, maxNativeZoom: 18
          }),
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', {
            attribution: '©Esri', maxZoom: 19, opacity: 0.8
          }),
        ]),
        topo: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
          attribution: '©OpenTopoMap', maxZoom: 17
        }),
      }
      tiles.satellite.addTo(map)
      tileLayers.current = tiles
      L.control.zoom({ position: 'bottomright' }).addTo(map)

      // Bidirectional bounds callback — fires on moveend/zoomend
      function fireBounds() {
        if (!onBoundsChange) return
        const b = map.getBounds()
        onBoundsChange({
          north: b.getNorth(), south: b.getSouth(),
          east:  b.getEast(),  west:  b.getWest()
        })
      }
      map.on('moveend', fireBounds)
      map.on('zoomend', fireBounds)

      instanceRef.current = { map, L }
      // Use ResizeObserver to detect when container actually reaches full size
      const ro = new ResizeObserver(() => { map.invalidateSize() })
      ro.observe(mapRef.current)
      setTimeout(() => map.invalidateSize(), 50)
      setTimeout(() => map.invalidateSize(), 300)
    })

    return () => {
      if (instanceRef.current?.map) {
        instanceRef.current.map.remove()
        instanceRef.current = null
      }
    }
  }, [])

  // Switch tile layer
  useEffect(() => {
    if (!instanceRef.current) return
    const { map } = instanceRef.current
    Object.values(tileLayers.current).forEach(t => {
      try { map.removeLayer(t) } catch {}
    })
    if (tileLayers.current[layer]) tileLayers.current[layer].addTo(map)
  }, [layer])

  // Render markers
  useEffect(() => {
    if (!instanceRef.current || !records) return
    const { map, L } = instanceRef.current
    Object.values(markersRef.current).forEach(m => { try { map.removeLayer(m) } catch {} })
    markersRef.current = {}

    records.forEach(rec => {
      if (!rec.gps_latitude || !rec.gps_longitude) return
      const d       = rec.ai_distance
      const isLead  = d !== null && d !== undefined && d < 0.35
      const isVerif = rec.user_verified_status?.includes('CONFIRMED')
      const color   = isLead ? '#f85149' : '#3fb950'
      const ring    = isLead ? 'rgba(248,81,73,0.2)' : 'rgba(63,185,80,0.15)'
      const size    = isLead ? 12 : 9

      const icon = L.divIcon({
        className: '',
        html: `<div style="position:relative;width:${size+8}px;height:${size+8}px;display:flex;align-items:center;justify-content:center">
          ${isLead ? `<div style="position:absolute;width:${size+8}px;height:${size+8}px;border-radius:50%;background:${ring};animation:ping 2s cubic-bezier(0,0,0.2,1) infinite"></div>` : ''}
          <div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:1.5px solid rgba(255,255,255,0.5);box-shadow:0 0 6px ${color}66;position:relative;z-index:1;cursor:pointer"></div>
        </div>
        <style>@keyframes ping{75%,100%{transform:scale(1.8);opacity:0}}</style>`,
        iconSize: [size+8, size+8], iconAnchor: [(size+8)/2, (size+8)/2],
      })

      const marker = L.marker([rec.gps_latitude, rec.gps_longitude], { icon })
        .addTo(map)
        .bindPopup(`
          <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;line-height:1.7;min-width:160px;background:#1c2128;color:#e6edf3;border-radius:4px;padding:2px">
            <div style="font-weight:700;font-size:12px;margin-bottom:4px;color:#388bfd">SL-${rec.service_line_id} · EV-${rec.evidence_id}</div>
            <div style="color:${color};font-weight:600">${isLead ? '⚠ Lead Suspect' : '✓ Clear'}${d !== null && d !== undefined ? ` (${Number(d).toFixed(4)})` : ''}</div>
            <div style="color:#8b949e;font-size:10px;margin-top:2px">${rec.gps_latitude.toFixed(5)}, ${rec.gps_longitude.toFixed(5)}</div>
            ${isVerif ? `<div style="color:#3fb950;font-size:10px">✓ Inspector Verified</div>` : ''}
          </div>
        `, {
          offset: [0, -6],
          className: 'dark-popup'
        })
        .on('click', () => onSelect(rec))

      markersRef.current[rec.evidence_id] = marker
    })
  }, [records])

  // Pan to selected
  useEffect(() => {
    if (!instanceRef.current || selectedId == null) return
    const marker = markersRef.current[selectedId]
    if (marker) {
      instanceRef.current.map.setView(marker.getLatLng(), 16, { animate: true })
      marker.openPopup()
    }
  }, [selectedId])

  const suspects = records?.filter(r => r.ai_distance !== null && r.ai_distance < 0.35).length || 0
  const safe     = records?.filter(r => r.ai_distance !== null && r.ai_distance >= 0.35).length || 0

  return (
    <div className={styles.wrap}>
      <div className={styles.controls}>
        <div className={styles.controlsLeft}>
          <span className={styles.layerLabel}>BASEMAP</span>
          {[
            { key: 'street',    label: 'Dark' },
            { key: 'satellite', label: 'Satellite' },
            { key: 'hybrid',    label: 'Hybrid' },
            { key: 'topo',      label: 'Topo' },
          ].map(l => (
            <button
              key={l.key}
              className={`${styles.layerBtn} ${layer === l.key ? styles.layerActive : ''}`}
              onClick={() => setLayer(l.key)}
            >
              {l.label}
            </button>
          ))}
        </div>
        <div className={styles.controlsRight}>
          <span className={styles.mapInfo}>
            {records?.length ?? 0} nodes ·
            <span style={{ color: 'var(--danger)', marginLeft: 4 }}>{suspects} suspect</span> ·
            <span style={{ color: 'var(--success)', marginLeft: 4 }}>{safe} clear</span>
          </span>
        </div>
      </div>

      <div ref={mapRef} className={styles.map} />

      <style>{`
        .dark-popup .leaflet-popup-content-wrapper {
          background: #1c2128 !important;
          border: 1px solid rgba(255,255,255,0.1) !important;
          border-radius: 4px !important;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
          color: #e6edf3 !important;
        }
        .dark-popup .leaflet-popup-tip { background: #1c2128 !important; }
      `}</style>

      <div className={styles.legend}>
        <div className={styles.legendTitle}>LEGEND</div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#f85149', boxShadow: '0 0 4px #f8514966' }} />
          Lead Suspect
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#3fb950' }} />
          Clear / Safe
        </div>
        {onBoundsChange && (
          <div style={{ fontSize: 8, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
            Pan map to filter records
          </div>
        )}
      </div>
    </div>
  )
}
