// LoginPage.jsx — OKW FieldSync Login
import React, { useState } from 'react'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form
      })
      const data = await res.json()
      if (res.ok) {
        onLogin(data)
      } else {
        setError(data.detail || 'Invalid username or password')
      }
    } catch {
      setError('Cannot reach server — is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      height: '100vh', width: '100vw',
      background: '#0A2342',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Background grid pattern */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.04,
        backgroundImage: 'linear-gradient(#0891B2 1px, transparent 1px), linear-gradient(90deg, #0891B2 1px, transparent 1px)',
        backgroundSize: '40px 40px'
      }} />

      <div style={{ position: 'relative', width: '100%', maxWidth: 420, padding: '0 20px' }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: 'rgba(8,145,178,0.12)', border: '1px solid rgba(8,145,178,0.3)',
            borderRadius: 12, padding: '10px 20px', marginBottom: 16
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2C8.5 2 5 5 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-4-3.5-7-7-7z" fill="#0891B2"/>
              <circle cx="12" cy="9" r="2.5" fill="white"/>
            </svg>
            <span style={{ fontSize: 16, fontWeight: 800, color: '#fff', letterSpacing: '0.05em' }}>OKW FieldSync</span>
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            EPA LCRI Compliance Platform
          </div>
        </div>

        {/* Login card */}
        <div style={{
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 16, padding: 32,
          backdropFilter: 'blur(12px)'
        }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 6 }}>Sign in</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 24 }}>
            Access your utility's compliance dashboard
          </div>

          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 6 }}>
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                style={{
                  width: '100%', padding: '11px 14px',
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: 8, color: '#fff', fontSize: 14,
                  outline: 'none', boxSizing: 'border-box',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 6 }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                style={{
                  width: '100%', padding: '11px 14px',
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: 8, color: '#fff', fontSize: 14,
                  outline: 'none', boxSizing: 'border-box',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            {error && (
              <div style={{
                marginBottom: 16, padding: '10px 14px',
                background: 'rgba(220,38,38,0.12)',
                border: '1px solid rgba(220,38,38,0.3)',
                borderRadius: 8, fontSize: 12, color: '#f87171'
              }}>
                ⚠ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '12px',
                background: loading ? 'rgba(8,145,178,0.4)' : '#0891B2',
                border: 'none', borderRadius: 8,
                color: '#fff', fontSize: 14, fontWeight: 700,
                cursor: loading ? 'default' : 'pointer',
                fontFamily: 'inherit', transition: 'background 0.2s'
              }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Credentials hint for demo */}
        <div style={{
          marginTop: 16, padding: '12px 16px',
          background: 'rgba(8,145,178,0.08)',
          border: '1px solid rgba(8,145,178,0.2)',
          borderRadius: 10
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#0891B2', letterSpacing: '0.08em', marginBottom: 6 }}>
            DEMO CREDENTIALS
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', lineHeight: 1.8, fontFamily: 'monospace' }}>
            admin / OKW_Admin_2026!<br/>
            inspector1 / Inspector_2026!
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 20, fontSize: 10, color: 'rgba(255,255,255,0.2)' }}>
          OKW FieldSync v3.0 · PWSID OK1020401 · ODEQ 2026
        </div>
      </div>
    </div>
  )
}
