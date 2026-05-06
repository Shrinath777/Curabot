import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/useAuthStore'
import { api } from '../services/api'

const DashboardPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()
  const [sessions, setSessions] = useState<any[]>([])
  const [diagnoses, setDiagnoses] = useState<any[]>([])

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return }
    loadData()
  }, [isAuthenticated])

  const loadData = async () => {
    try {
      const [sessRes, diagRes] = await Promise.all([
        api.get('/api/sessions', { headers: { 'x-user-id': user?.user_id || '' } }),
        api.get('/api/diagnoses', { headers: { 'x-user-id': user?.user_id || '' } }),
      ])
      setSessions(sessRes.data?.sessions || [])
      setDiagnoses(diagRes.data?.diagnoses || [])
    } catch { /* silent */ }
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <div className="cyber-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="gradient-orb orb-3" />
        <div className="grid-overlay" />
      </div>

      <div style={{ position: 'relative', zIndex: 5, maxWidth: 1100, margin: '0 auto', padding: '2rem' }}>
        {/* Nav */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-card-static"
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1.25rem', marginBottom: '2rem', borderRadius: 'var(--radius-lg)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => navigate('/')}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>⚕️</div>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>CuraBot</span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button className="btn-ghost" onClick={() => navigate('/profile')}>Profile</button>
            <button className="btn-ghost" onClick={() => navigate('/about')}>About</button>
            <button className="btn-ghost" onClick={() => { logout(); navigate('/') }}>Logout</button>
          </div>
        </motion.div>

        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '2rem', marginBottom: '0.5rem' }}>
            Welcome, {user?.full_name || 'Doctor'}
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Your clinical reasoning dashboard</p>
        </motion.div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { icon: '💬', label: 'Sessions', value: sessions.length, color: 'var(--color-primary)' },
            { icon: '📋', label: 'Diagnoses', value: diagnoses.length, color: 'var(--color-cyan)' },
            { icon: '🤖', label: 'Agents', value: 6, color: 'var(--color-emerald)' },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i }}
              className="glass-card"
              style={{ textAlign: 'center', padding: '1.5rem' }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{stat.icon}</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{stat.label}</div>
            </motion.div>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card"
          style={{
            textAlign: 'center', padding: '3rem 2rem', marginBottom: '2rem',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(6,182,212,0.06))',
            border: '1px solid rgba(99,102,241,0.15)',
          }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: '0.75rem' }}>Start a New Diagnosis</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', maxWidth: 500, margin: '0 auto 1.5rem' }}>
            Describe symptoms and let 6 AI agents guide you through the differential diagnosis process
          </p>
          <button className="btn-primary" onClick={() => navigate('/chat')} style={{ fontSize: '1.05rem', padding: '1rem 3rem' }}>
            Begin Diagnosis →
          </button>
        </motion.div>

        {/* Recent Diagnoses */}
        {diagnoses.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass-card-static"
            style={{ marginBottom: '2rem' }}
          >
            <div className="section-title" style={{ marginBottom: '1rem' }}>📋 Recent Diagnoses</div>
            {diagnoses.slice(0, 5).map((dx: any, i: number) => {
              const topHyp = dx.final_hypotheses?.[0]
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.04)',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{topHyp?.name || 'Unknown'}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{dx.concluded_at?.split('T')[0] || ''}</div>
                  </div>
                  {topHyp && (
                    <span className="badge badge-primary">{topHyp.confidence}%</span>
                  )}
                </div>
              )
            })}
          </motion.div>
        )}

        {/* Footer */}
        <div className="disclaimer-banner">
          ⚠️ FOR MEDICAL EDUCATION ONLY — Not for clinical use
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
