// MapPanel.jsx — Leaflet map with layer controls + legend
import { useEffect, useRef, useState } from 'react'
import styles from './MapPanel.module.css'

export default function MapPanel({ records, selectedId, onSelect }) {
  const mapRef      = useRef(null)
  const instanceRef = useRef(null)
  const markersRef  = useRef({})
  const [layer, setLayer] = useState('satellite')
  const tileLayers = useRef({})

  useEffect(() => {
    if (instanceRef.current || !mapRef.current) return
    import('leaflet').then(L => {
      const map = L.map(mapRef.current, { center: [35.47, -97.52], zoom: 12, zoomControl: false })

      // Multiple tile layers
      const tiles = {
        voyager: L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          attribution: '©OpenStreetMap ©CartoDB', maxZoom: 19
        }),
        satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
          attribution: 'Tiles © Esri — Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
          maxZoom: 19, maxNativeZoom: 18
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
      tiles.voyager.addTo(map)
      tileLayers.current = tiles

      // Custom zoom control position
      L.control.zoom({ position: 'bottomright' }).addTo(map)

      instanceRef.current = { map, L }
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
    Object.values(tileLayers.current).forEach(t => map.removeLayer(t))
    if (tileLayers.current[layer]) tileLayers.current[layer].addTo(map)
  }, [layer])

  useEffect(() => {
    if (!instanceRef.current || !records) return
    const { map, L } = instanceRef.current
    Object.values(markersRef.current).forEach(m => map.removeLayer(m))
    markersRef.current = {}

    records.forEach(rec => {
      if (!rec.gps_latitude || !rec.gps_longitude) return
      const d      = rec.ai_distance
      const isLead = d !== null && d !== undefined && d < 0.35
      const color  = isLead ? '#DC2626' : '#16A34A'
      const ring   = isLead ? 'rgba(220,38,38,0.2)' : 'rgba(22,163,74,0.15)'

      const icon = L.divIcon({
        className: '',
        html: `<div style="position:relative;width:20px;height:20px;display:flex;align-items:center;justify-content:center">
          <div style="position:absolute;width:20px;height:20px;border-radius:50%;background:${ring};animation:ping 2s cubic-bezier(0,0,0.2,1) infinite"></div>
          <div style="width:10px;height:10px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3);position:relative;z-index:1;cursor:pointer"></div>
        </div>
        <style>@keyframes ping{75%,100%{transform:scale(1.8);opacity:0}}</style>`,
        iconSize: [20, 20], iconAnchor: [10, 10],
      })

      const marker = L.marker([rec.gps_latitude, rec.gps_longitude], { icon })
        .addTo(map)
        .bindPopup(`
          <div style="font-family:IBM Plex Mono,monospace;font-size:11px;line-height:1.7;min-width:160px">
            <div style="font-weight:700;font-size:12px;margin-bottom:4px;color:#0062BD">
              SL-${rec.service_line_id} · EV-${rec.evidence_id}
            </div>
            <div style="color:${color};font-weight:600">
              ${isLead ? '⚠ Lead Suspect' : '✓ Clear'}
              ${d !== null && d !== undefined ? ` (${Number(d).toFixed(4)})` : ''}
            </div>
            <div style="color:#6B7280;font-size:10px;margin-top:2px">
              ${rec.gps_latitude.toFixed(5)}, ${rec.gps_longitude.toFixed(5)}
            </div>
          </div>
        `, { offset: [0, -8] })
        .on('click', () => onSelect(rec))

      markersRef.current[rec.evidence_id] = marker
    })
  }, [records])

  useEffect(() => {
    if (!instanceRef.current || selectedId == null) return
    const marker = markersRef.current[selectedId]
    if (marker) {
      instanceRef.current.map.setView(marker.getLatLng(), 15, { animate: true })
      marker.openPopup()
    }
  }, [selectedId])

  const suspects = records?.filter(r => r.ai_distance !== null && r.ai_distance < 0.35).length || 0
  const safe     = records?.filter(r => r.ai_distance !== null && r.ai_distance >= 0.35).length || 0

  return (
    <div className={styles.wrap}>
      {/* Map controls bar */}
      <div className={styles.controls}>
        <div className={styles.controlsLeft}>
          <span className={styles.layerLabel}>Base Map:</span>
          {[
            { key: 'voyager',   label: 'Street' },
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
            {records?.length ?? 0} nodes · {suspects} suspect · {safe} clear
          </span>
        </div>
      </div>

      {/* Map */}
      <div ref={mapRef} className={styles.map} />

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendTitle}>Legend</div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{background:'#DC2626'}} />
          Lead Suspect (&lt;0.35)
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{background:'#16A34A'}} />
          Clear (≥0.35)
        </div>
      </div>
    </div>
  )
}