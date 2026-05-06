import React from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

const AboutPage: React.FC = () => {
  const navigate = useNavigate()

  const pipeline = [
    { num: '01', name: 'Symptom Normalizer', desc: 'Converts free-text descriptions into standardized medical concepts. Identifies primary/secondary symptoms, severity, and duration.', icon: '🔬', color: '#6366f1' },
    { num: '02', name: 'Hypothesis Generator', desc: 'Creates a broad differential diagnosis with initial Bayesian priors. Considers disease prevalence, symptom specificity, and must-not-miss emergencies.', icon: '🧠', color: '#8b5cf6' },
    { num: '03', name: 'Evidence Evaluator', desc: 'Maps every finding to supporting or contradicting evidence per hypothesis. Maintains a transparent evidence ledger with strength ratings.', icon: '📊', color: '#06b6d4' },
    { num: '04', name: 'Hypothesis Reviser', desc: 'Updates confidence scores using Bayesian-inspired reasoning. Explicitly explains why each hypothesis was promoted, demoted, or held stable.', icon: '🔄', color: '#22d3ee' },
    { num: '05', name: 'Diagnostic Strategist', desc: 'Generates dynamic questions to maximize information gain — NO predefined question scripts. Determines when to request vitals and when to conclude.', icon: '🎯', color: '#10b981' },
    { num: '06', name: 'Bias Detector', desc: 'Checks for anchoring bias, confirmation bias, premature closure, and availability bias. Forces the system to consider alternative diagnoses.', icon: '⚖️', color: '#34d399' },
  ]

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <div className="cyber-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="gradient-orb orb-3" />
        <div className="gradient-orb orb-4" />
        <div className="grid-overlay" />
      </div>

      <div style={{ position: 'relative', zIndex: 5, maxWidth: 900, margin: '0 auto', padding: '2rem' }}>
        {/* Nav */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}
        >
          <button className="btn-ghost" onClick={() => navigate(-1)}>← Back</button>
          <button className="btn-primary" onClick={() => navigate('/chat')} style={{ padding: '0.6rem 1.5rem' }}>Try It →</button>
        </motion.div>

        {/* Title */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h1 style={{
            fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'clamp(2rem, 4vw, 3rem)',
            marginBottom: '1rem',
            background: 'linear-gradient(135deg, #fff, #a78bfa, #22d3ee)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            How CuraBot Works
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: 600, margin: '0 auto', lineHeight: 1.7 }}>
            6 specialized AI agents collaborate in a pipeline to model real clinical diagnostic reasoning
          </p>
        </motion.div>

        {/* Disclaimer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-card-static"
          style={{
            marginBottom: '3rem', padding: '1.5rem',
            background: 'rgba(245,158,11,0.06)',
            border: '1px solid rgba(245,158,11,0.15)',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--color-amber)', marginBottom: '0.5rem' }}>⚠️ Medical Education Only</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            CuraBot is designed for clinical reasoning training. It does NOT provide real diagnoses, treatment recommendations, or clinical decisions. Always consult qualified healthcare professionals for medical concerns.
          </p>
        </motion.div>

        {/* Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '3rem' }}>
          {pipeline.map((agent, i) => (
            <motion.div
              key={agent.num}
              initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.1 }}
              className="glass-card"
              style={{ display: 'flex', gap: '1.25rem', alignItems: 'flex-start' }}
            >
              <div style={{
                width: 56, height: 56, borderRadius: 16, flexShrink: 0,
                background: `${agent.color}20`, border: `1px solid ${agent.color}30`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.5rem',
              }}>
                {agent.icon}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.7rem', color: agent.color, fontWeight: 700 }}>{agent.num}</span>
                  <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem' }}>{agent.name}</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{agent.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Key Concepts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="glass-card-static"
          style={{ marginBottom: '3rem', padding: '2rem' }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: '1.5rem' }}>🎓 Clinical Reasoning Principles</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
            {[
              { title: 'Bayesian Updating', desc: 'Confidence adjusts as new evidence arrives' },
              { title: 'Differential Diagnosis', desc: 'Multiple competing hypotheses, not a single answer' },
              { title: 'Information Gain', desc: 'Questions target maximum uncertainty reduction' },
              { title: 'Bias Awareness', desc: 'Active detection of cognitive shortcuts' },
              { title: 'Evidence Tracking', desc: 'Transparent for/against ledger for each hypothesis' },
              { title: 'Staged Revelation', desc: 'New info changes the diagnostic picture over time' },
            ].map(c => (
              <div key={c.title} style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.3rem' }}>{c.title}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>{c.desc}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Diseases */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="glass-card-static"
          style={{ marginBottom: '2rem' }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: '1rem' }}>🏥 Starter Disease Coverage</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Deep clinical knowledge for the chest pain differential:
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            {[
              { name: 'Acute Myocardial Infarction', emoji: '❤️', type: 'Cardiac' },
              { name: 'GERD', emoji: '🔥', type: 'Gastric' },
              { name: 'Pneumonia', emoji: '🫁', type: 'Respiratory' },
              { name: 'Pulmonary Embolism', emoji: '🩸', type: 'Vascular' },
            ].map(d => (
              <div key={d.name} style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.85rem', background: 'rgba(255,255,255,0.02)',
                borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.05)',
              }}>
                <span style={{ fontSize: '1.5rem' }}>{d.emoji}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{d.name}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{d.type}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        <div className="disclaimer-banner">
          ⚠️ FOR MEDICAL EDUCATION ONLY — Not for clinical use
        </div>
      </div>
    </div>
  )
}

export default AboutPage
