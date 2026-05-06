import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/useAuthStore'

const LandingPage: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard')
  }, [isAuthenticated])

  const agents = [
    { icon: '🔬', name: 'Symptom Normalizer', desc: 'Converts free-text into standardized medical concepts' },
    { icon: '🧠', name: 'Hypothesis Generator', desc: 'Creates differential diagnosis with Bayesian priors' },
    { icon: '📊', name: 'Evidence Evaluator', desc: 'Maps findings to supporting & contradicting evidence' },
    { icon: '🔄', name: 'Hypothesis Reviser', desc: 'Updates confidence as evidence evolves' },
    { icon: '🎯', name: 'Diagnostic Strategist', desc: 'Dynamic questions to maximize information gain' },
    { icon: '⚖️', name: 'Bias Detector', desc: 'Flags anchoring, confirmation bias, premature closure' },
  ]

  const features = [
    { icon: '💬', title: 'Dynamic Conversations', desc: 'AI-driven questions adapt in real-time — no scripts, no templates' },
    { icon: '📈', title: 'Confidence Tracking', desc: 'Watch hypotheses rise and fall as evidence accumulates' },
    { icon: '🔍', title: 'Evidence Ledger', desc: 'Transparent for/against tracking for every finding' },
    { icon: '👤', title: 'Context-Aware', desc: 'Returning users get personalized diagnosis informed by history' },
  ]

  return (
    <div style={{ position: 'relative', zIndex: 1, minHeight: '100vh' }}>
      {/* Background */}
      <div className="cyber-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="gradient-orb orb-3" />
        <div className="gradient-orb orb-4" />
        <div className="grid-overlay" />
      </div>

      {/* Top Nav */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={{
          position: 'relative', zIndex: 10,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '1.5rem 3rem',
          background: 'rgba(255,255,255,0.02)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12,
            background: 'var(--accent-primary)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem',
          }}>⚕️</div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.35rem' }}>CuraBot</span>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn-ghost" onClick={() => navigate('/login')}>Log In</button>
          <button className="btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
        </div>
      </motion.nav>

      {/* Hero */}
      <div style={{ position: 'relative', zIndex: 5, maxWidth: 1200, margin: '0 auto', padding: '0 2rem' }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          style={{ textAlign: 'center', paddingTop: '5rem' }}
        >
          <span className="badge badge-medical" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
            ⚠️ For Medical Education Only
          </span>
          <h1 style={{
            fontFamily: 'var(--font-display)', fontWeight: 800,
            fontSize: 'clamp(2.5rem, 5vw, 4rem)', lineHeight: 1.1,
            marginBottom: '1.5rem',
            background: 'linear-gradient(135deg, #fff 0%, #a78bfa 50%, #22d3ee 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            AI-Powered Differential<br />Diagnosis Tutor
          </h1>
          <p style={{
            fontSize: '1.15rem', color: 'var(--text-secondary)',
            maxWidth: 650, margin: '0 auto 2.5rem',
            lineHeight: 1.7,
          }}>
            6 specialized AI agents work together to analyze symptoms, generate hypotheses,
            track evidence, and teach clinical reasoning — just like a real diagnostic process.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary" onClick={() => navigate('/signup')}
              style={{ fontSize: '1.05rem', padding: '1rem 2.5rem' }}>
              Start Diagnosis →
            </button>
            <button className="btn-secondary" onClick={() => navigate('/about')}
              style={{ fontSize: '1.05rem', padding: '1rem 2.5rem' }}>
              How It Works
            </button>
          </div>
        </motion.div>

        {/* Agent Cards */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '1rem', marginTop: '5rem',
          }}
        >
          {agents.map((agent, i) => (
            <motion.div
              key={agent.name}
              className="glass-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.08 }}
              style={{ textAlign: 'center', padding: '1.5rem 1rem' }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{agent.icon}</div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.5rem' }}>{agent.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{agent.desc}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.6 }}
          style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '1.5rem', margin: '5rem 0',
          }}
        >
          {features.map((f, i) => (
            <div key={f.title} className="glass-card" style={{ padding: '2rem' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>{f.icon}</div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: '0.5rem' }}>{f.title}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </motion.div>

        {/* Footer */}
        <div style={{
          textAlign: 'center', padding: '2rem 0 3rem',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          color: 'var(--text-muted)', fontSize: '0.8rem',
        }}>
          ⚠️ FOR MEDICAL EDUCATION ONLY — Not for clinical use • CuraBot v2.0 • 6 AI Agents
        </div>
      </div>
    </div>
  )
}

export default LandingPage
