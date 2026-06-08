// useData.js — polls FastAPI every 30s with JWT auth
import { useState, useEffect, useCallback } from 'react'

export function useData(token) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const fetch_ = useCallback(async () => {
    if (!token) return
    try {
      const res = await fetch('/api/evidence', {
        headers: { 'Authorization': 'Bearer ' + token }
      })
      if (res.status === 401) {
        setError('Session expired — please log in again')
        return
      }
      if (!res.ok) throw new Error('HTTP ' + res.status)
      const json = await res.json()
      setData(json)
      setError(null)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    fetch_()
    const interval = setInterval(fetch_, 30000)
    return () => clearInterval(interval)
  }, [fetch_])

  return { data, loading, error, refresh: fetch_, lastRefresh }
}
