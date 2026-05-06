import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDiagnosticStore } from '../store/useDiagnosticStore'
import { useAuthStore } from '../store/useAuthStore'

interface Message {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
}

const ChatPage: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()
  const {
    hypotheses, evidence, suggestions, biasFlags, agentThoughts,
    loading, error, sendMessage, resetSession,
    needMoreInfo, requestVitals, vitalsNeeded,
    confidenceTrajectory, revisionNarrative,
    shouldConclude, conclusionMessage, finalRecommendations, iteration,
    sessionId,
  } = useDiagnosticStore()

  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hello! I'm CuraBot, your AI differential diagnosis tutor. Describe the symptoms you'd like to explore, and I'll guide you through the diagnostic reasoning process.",
      sender: 'bot',
      timestamp: new Date(),
    }
  ])
  const [showVitals, setShowVitals] = useState(false)
  const [vitals, setVitals] = useState({
    blood_pressure: '',
    heart_rate: '',
    temperature: '',
    respiratory_rate: '',
    oxygen_saturation: '',
  })

  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [isUploading, setIsUploading] = useState(false)
  const [showUploadPanel, setShowUploadPanel] = useState(false)
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, agentThoughts])

  useEffect(() => {
    if (requestVitals) setShowVitals(true)
  }, [requestVitals])

  const handleSend = async () => {
    if (!message.trim() || loading) return
    const userMsg: Message = { id: Date.now().toString(), text: message, sender: 'user', timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    const currentMessage = message
    setMessage('')

    const botText = await sendMessage(currentMessage, user?.user_id)
    if (botText) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: botText, sender: 'bot', timestamp: new Date() }])
    }
    inputRef.current?.focus()
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('report_type', 'lab_result')

    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE}/api/upload-record`, {
        method: 'POST',
        headers: {
          'x-user-id': user?.user_id || 'anonymous'
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to upload record')
      }

      const result = await response.json()
      
      // Check results for partial success
      if (result.indexing_status === 'failed') {
        setMessages(prev => [...prev, { 
          id: Date.now().toString(), 
          text: `Medical record "${file.name}" uploaded to Supabase, but automatic AI analysis failed. Our engineers will re-process it shortly. You can manually describe any key findings in the chat for now.`, 
          sender: 'bot', 
          timestamp: new Date() 
        }])
      } else {
        // Full success
        setMessages(prev => [...prev, { 
          id: Date.now().toString(), 
          text: `Medical record "${file.name}" uploaded successfully. ${result.indexed_chunks || 0} context chunks mapped to your profile. The agents will now consider this evidence.`, 
          sender: 'bot', 
          timestamp: new Date() 
        }])
      }
    } catch (err) {
      console.error("Upload error:", err)
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        text: "Sorry, there was an error connecting to the medical server. Please check your internet or try again later.", 
        sender: 'bot', 
        timestamp: new Date() 
      }])
    } finally {
      setIsUploading(false)
      setShowUploadPanel(false)
      setSelectedFileName(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFileName(file.name)
  }

  const handleVitalsSubmit = async () => {
    const vitalsData: any = {}
    if (vitals.blood_pressure) vitalsData.blood_pressure = vitals.blood_pressure
    if (vitals.heart_rate) vitalsData.heart_rate = parseInt(vitals.heart_rate)
    if (vitals.temperature) vitalsData.temperature = parseFloat(vitals.temperature)
    if (vitals.respiratory_rate) vitalsData.respiratory_rate = parseInt(vitals.respiratory_rate)
    if (vitals.oxygen_saturation) vitalsData.oxygen_saturation = parseInt(vitals.oxygen_saturation)

    const summary = Object.entries(vitalsData).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join(', ')
    if (!summary) return

    setMessages(prev => [...prev, { id: Date.now().toString(), text: `Vitals: ${summary}`, sender: 'user', timestamp: new Date() }])
    setShowVitals(false)

    const botText = await sendMessage(`My vitals are: ${summary}`, user?.user_id, vitalsData)
    if (botText) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: botText, sender: 'bot', timestamp: new Date() }])
    }
  }

  const handleReset = () => {
    resetSession()
    setMessages([{
      id: '1',
      text: "Session reset. Describe new symptoms to begin a fresh diagnosis.",
      sender: 'bot',
      timestamp: new Date(),
    }])
  }

  const handleSuggestionClick = async (suggestion: string) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), text: suggestion, sender: 'user', timestamp: new Date() }])
    const botText = await sendMessage(suggestion, user?.user_id)
    if (botText) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: botText, sender: 'bot', timestamp: new Date() }])
    }
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      {/* Background */}
      <div className="cyber-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="gradient-orb orb-3" />
        <div className="gradient-orb orb-4" />
        <div className="grid-overlay" />
      </div>

      <div style={{ position: 'relative', zIndex: 5, maxWidth: 1440, margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', flexDirection: 'column', height: '100vh' }}>

        {/* Top Bar */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-card-static"
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1.25rem', marginBottom: '1rem', borderRadius: 'var(--radius-lg)' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>⚕️</div>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem' }}>CuraBot</span>
            <span className="badge badge-medical">Education Only</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {isAuthenticated && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {user?.full_name || user?.email}
              </span>
            )}
            <button className="btn-ghost" onClick={() => navigate('/dashboard')}>Dashboard</button>
            <button className="btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }} onClick={handleReset}>New Session</button>
            {isAuthenticated ? (
              <button className="btn-ghost" onClick={logout}>Logout</button>
            ) : (
              <button className="btn-ghost" onClick={() => navigate('/login')}>Login</button>
            )}
          </div>
        </motion.div>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px 280px', gap: '1rem', flex: 1, overflow: 'hidden' }}>

          {/* Left: Chat */}
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="glass-card-static"
            style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}
          >
            {/* Chat Header */}
            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className="section-title" style={{ marginBottom: 0 }}>
                💬 Clinical Conversation
                <span>Iteration {iteration}</span>
              </div>
              {!needMoreInfo && (
                <span className="badge badge-success">✓ Diagnosis Complete</span>
              )}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflow: 'auto', padding: '1rem 1.25rem' }}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    display: 'flex',
                    justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '0.75rem',
                  }}
                >
                  <div style={{
                    maxWidth: '80%',
                    padding: '0.85rem 1.15rem',
                    borderRadius: msg.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    background: msg.sender === 'user'
                      ? 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.2))'
                      : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${msg.sender === 'user' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)'}`,
                    backdropFilter: 'blur(8px)',
                    fontSize: '0.9rem',
                    lineHeight: 1.6,
                    color: 'var(--text-primary)',
                  }}>
                    {msg.text}
                  </div>
                </motion.div>
              ))}

              {/* Agent Thoughts */}
              <AnimatePresence>
                {loading && agentThoughts.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    style={{ marginTop: '0.5rem' }}
                  >
                    {agentThoughts.filter(t => t.status === 'processing' || t.status === 'completed').slice(-3).map((t, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                        padding: '0.4rem 0.75rem', marginBottom: '0.3rem',
                        fontSize: '0.75rem', color: 'var(--text-muted)',
                        borderLeft: `2px solid ${t.status === 'completed' ? 'var(--color-emerald)' : 'var(--color-amber)'}`,
                      }}>
                        <span className={`status-dot ${t.status}`} />
                        <strong style={{ color: 'var(--text-secondary)' }}>{t.agent}:</strong> {t.thought}
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Loading */}
              {loading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.75rem' }}>
                  <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }} />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Agents analyzing...</span>
                </div>
              )}

              {/* Conclusion */}
              {shouldConclude && conclusionMessage && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{
                    background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                    borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginTop: '1rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--color-emerald)', marginBottom: '0.5rem' }}>📋 Diagnosis Summary</div>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>{conclusionMessage}</p>
                  {finalRecommendations.length > 0 && (
                    <div style={{ marginTop: '0.75rem' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Next Steps:</div>
                      {finalRecommendations.map((r, i) => (
                        <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: '0.75rem' }}>• {r}</div>
                      ))}
                    </div>
                  )}

                  {/* Download Report Buttons */}
                  {sessionId && (
                    <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => {
                          const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                          window.open(`${API_BASE}/api/report/html/${sessionId}`, '_blank')
                        }}
                        style={{
                          background: 'linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.2))',
                          border: '1px solid rgba(99,102,241,0.3)',
                          borderRadius: 'var(--radius-md)',
                          padding: '0.6rem 1.2rem',
                          color: 'var(--color-primary-light)',
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          display: 'flex', alignItems: 'center', gap: '0.4rem',
                          transition: 'all 0.2s',
                        }}
                      >
                        📄 Download PDF Report
                      </button>
                      <button
                        onClick={() => {
                          const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                          const link = document.createElement('a')
                          link.href = `${API_BASE}/api/report/json/${sessionId}`
                          link.download = `curabot_report_${sessionId.slice(0, 8)}.json`
                          link.click()
                        }}
                        style={{
                          background: 'rgba(16,185,129,0.1)',
                          border: '1px solid rgba(16,185,129,0.25)',
                          borderRadius: 'var(--radius-md)',
                          padding: '0.6rem 1.2rem',
                          color: 'var(--color-emerald)',
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          display: 'flex', alignItems: 'center', gap: '0.4rem',
                          transition: 'all 0.2s',
                        }}
                      >
                        📦 Download JSON Data
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Vitals Input Panel */}
            <AnimatePresence>
              {showVitals && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  style={{
                    borderTop: '1px solid var(--glass-border)',
                    padding: '1rem 1.25rem',
                    background: 'rgba(6,182,212,0.04)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-cyan)' }}>📊 Enter Vital Signs</span>
                    <button className="btn-ghost" onClick={() => setShowVitals(false)} style={{ fontSize: '0.75rem' }}>✕ Close</button>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem' }}>
                    {[
                      { key: 'blood_pressure', label: 'BP (mmHg)', placeholder: '120/80' },
                      { key: 'heart_rate', label: 'Heart Rate', placeholder: '72 bpm' },
                      { key: 'temperature', label: 'Temp (°F)', placeholder: '98.6' },
                      { key: 'respiratory_rate', label: 'Resp Rate', placeholder: '16/min' },
                      { key: 'oxygen_saturation', label: 'SpO2 (%)', placeholder: '98' },
                    ].map(v => (
                      <div key={v.key}>
                        <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>{v.label}</label>
                        <input
                          className="glass-input"
                          style={{ padding: '0.5rem 0.75rem', fontSize: '0.8rem' }}
                          placeholder={v.placeholder}
                          value={(vitals as any)[v.key]}
                          onChange={e => setVitals({ ...vitals, [v.key]: e.target.value })}
                        />
                      </div>
                    ))}
                  </div>
                  <button className="btn-primary" onClick={handleVitalsSubmit} style={{ marginTop: '0.75rem', padding: '0.5rem 1.5rem', fontSize: '0.85rem' }}>
                    Submit Vitals
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Upload Records Panel — only for logged-in users */}
            {isAuthenticated && (
              <AnimatePresence>
                {showUploadPanel && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    style={{
                      borderTop: '1px solid var(--glass-border)',
                      padding: '1rem 1.25rem',
                      background: 'rgba(139,92,246,0.04)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#a78bfa' }}>📄 Import Medical Records</span>
                      <button className="btn-ghost" onClick={() => setShowUploadPanel(false)} style={{ fontSize: '0.75rem' }}>✕ Close</button>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Upload a PDF lab report or medical document. The AI agents will analyse it alongside your symptoms.
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <input 
                          type="file" 
                          ref={fileInputRef} 
                          onChange={handleFileSelect} 
                          accept=".pdf" 
                          style={{ display: 'none' }} 
                        />
                        <button 
                          className="btn-secondary" 
                          onClick={() => fileInputRef.current?.click()}
                          disabled={isUploading}
                          style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}
                        >
                          Choose File...
                        </button>
                        <span style={{ fontSize: '0.8rem', color: selectedFileName ? 'var(--color-primary-light)' : 'var(--text-muted)' }}>
                          {selectedFileName || 'No file selected'}
                        </span>
                      </div>

                      <button 
                        className="btn-primary" 
                        onClick={() => handleFileUpload({ target: fileInputRef.current } as any)} 
                        disabled={!selectedFileName || isUploading}
                        style={{ padding: '0.5rem 1.5rem', fontSize: '0.85rem', width: 'fit-content', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                      >
                        {isUploading ? <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> : '📤'}
                        Import to Analysis
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            )}

            {/* Suggestions */}
            {suggestions.length > 0 && !shouldConclude && (
              <div style={{ padding: '0.5rem 1.25rem', borderTop: '1px solid var(--glass-border)' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {suggestions.map((s, i) => (
                    <button key={i} onClick={() => handleSuggestionClick(s)} style={{
                      background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                      borderRadius: 'var(--radius-full)', padding: '0.35rem 0.85rem',
                      color: 'var(--color-primary-light)', fontSize: '0.78rem',
                      cursor: 'pointer', transition: 'all 0.2s',
                    }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '0.5rem' }}>
              <button
                className="btn-ghost"
                onClick={() => setShowVitals(!showVitals)}
                title="Enter Vital Signs"
                style={{ fontSize: '1.1rem', padding: '0.5rem', background: showVitals ? 'rgba(6,182,212,0.1)' : 'transparent' }}
              >
                🩺
              </button>
              
              {/* PDF Upload button — only for logged-in users */}
              {isAuthenticated && (
                <button
                  className="btn-ghost"
                  onClick={() => setShowUploadPanel(!showUploadPanel)}
                  title="Upload PDF Medical Record"
                  style={{ fontSize: '1.1rem', padding: '0.5rem', background: showUploadPanel ? 'rgba(139,92,246,0.1)' : 'transparent' }}
                >
                  📄
                </button>
              )}
              
              <input
                ref={inputRef}
                type="text"
                className="glass-input"
                placeholder="Describe your symptoms..."
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                disabled={loading}
                style={{ flex: 1 }}
              />
              <button className="btn-primary" onClick={handleSend} disabled={!message.trim() || loading}
                style={{ padding: '0.75rem 1.5rem' }}>
                Send
              </button>
            </div>
          </motion.div>

          {/* Middle: Hypotheses & Agents */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflow: 'auto' }}>
            {/* Agent Status */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="glass-card-static"
            >
              <div className="section-title">🤖 Agent Pipeline <span>6 Active</span></div>
              {['Symptom Normalizer', 'Hypothesis Generator', 'Evidence Evaluator', 'Hypothesis Reviser', 'Diagnostic Strategist', 'Self-Critique'].map(agent => {
                const thought = [...agentThoughts].reverse().find((t: any) => t.agent === agent) as any
                const status = thought?.status || 'idle'
                return (
                  <div key={agent} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                    padding: '0.45rem 0', borderBottom: '1px solid rgba(255,255,255,0.03)',
                  }}>
                    <span className={`status-dot ${status}`} style={{ marginTop: '0.35rem', flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{agent}</div>
                      {thought && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {thought.thought}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </motion.div>

            {/* Hypotheses */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="glass-card-static"
            >
              <div className="section-title">📋 Differential Diagnosis</div>
              {hypotheses.length > 0 ? hypotheses.map((h, idx) => (
                <div key={h.name} style={{
                  padding: '0.75rem',
                  background: idx === 0 ? 'rgba(99,102,241,0.08)' : 'transparent',
                  border: idx === 0 ? '1px solid rgba(99,102,241,0.15)' : '1px solid transparent',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '0.5rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                      {idx === 0 && '🥇 '}{idx === 1 && '🥈 '}{idx === 2 && '🥉 '}{h.name}
                    </span>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: idx === 0 ? 'var(--color-primary-light)' : 'var(--text-secondary)' }}>
                      {h.confidence}%
                    </span>
                  </div>
                  <div className="confidence-bar">
                    <div className="confidence-fill" style={{
                      width: `${h.confidence}%`,
                      background: idx === 0 ? 'var(--accent-primary)' : idx === 1 ? 'var(--accent-secondary)' : 'linear-gradient(90deg, #ec4899, #f43f5e)',
                    }} />
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                    <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>↑ {h.supporting}</span>
                    <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>↓ {h.contradicting}</span>
                  </div>
                  {h.reasoning && (
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.3rem', lineHeight: 1.5 }}>
                      {h.reasoning}
                    </div>
                  )}
                </div>
              )) : (
                <div className="empty-state">Describe symptoms to generate hypotheses</div>
              )}
            </motion.div>

            {/* Bias Alerts */}
            {biasFlags.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-card-static"
              >
                <div className="section-title">⚠️ Cognitive Bias Alerts</div>
                {biasFlags.map((b, i) => (
                  <div key={i} style={{
                    background: b.severity === 'high' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                    border: `1px solid ${b.severity === 'high' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)'}`,
                    borderRadius: 'var(--radius-md)', padding: '0.75rem', marginBottom: '0.5rem',
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', color: b.severity === 'high' ? '#f87171' : '#fbbf24' }}>{b.bias}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{b.description}</div>
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          {/* Right: Evidence & Info */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflow: 'auto' }}>
            {/* Evidence */}
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="glass-card-static"
            >
              <div className="section-title">🔍 Evidence Ledger</div>
              {evidence.length > 0 ? evidence.map((e, i) => (
                <div key={i} style={{
                  padding: '0.65rem', borderBottom: '1px solid rgba(255,255,255,0.03)',
                }}>
                  <div style={{ fontWeight: 600, fontSize: '0.82rem', textTransform: 'capitalize', marginBottom: '0.3rem' }}>
                    {(e.finding || '').replace(/_/g, ' ')}
                  </div>
                  {e.supports.length > 0 && (
                    <div style={{ marginBottom: '0.2rem' }}>
                      <span style={{ fontSize: '0.68rem', color: 'var(--color-emerald)', fontWeight: 600 }}>✓ Supports: </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{e.supports.join(', ')}</span>
                    </div>
                  )}
                  {e.contradicts.length > 0 && (
                    <div>
                      <span style={{ fontSize: '0.68rem', color: 'var(--color-rose)', fontWeight: 600 }}>✗ Against: </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{e.contradicts.join(', ')}</span>
                    </div>
                  )}
                </div>
              )) : (
                <div className="empty-state">No evidence yet</div>
              )}
            </motion.div>

            {/* Confidence Timeline */}
            {confidenceTrajectory.length > 1 && (
              <motion.div
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className="glass-card-static"
              >
                <div className="section-title">📈 Confidence Evolution</div>
                {confidenceTrajectory.map((snap, i) => (
                  <div key={i} style={{ marginBottom: '0.5rem', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Round {snap.iteration}</div>
                    {snap.hypotheses.slice(0, 3).map(h => (
                      <div key={h.name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '0.15rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{h.name.split(' ').pop()}</span>
                        <span style={{ color: 'var(--color-primary-light)', fontWeight: 600 }}>{h.confidence}%</span>
                      </div>
                    ))}
                  </div>
                ))}
              </motion.div>
            )}

            {/* Session Info */}
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="glass-card-static"
            >
              <div className="section-title">📊 Session Info</div>
              {[
                { label: 'Status', value: loading ? '⏳ Processing' : shouldConclude ? '✅ Complete' : '🟢 Ready' },
                { label: 'Iteration', value: iteration },
                { label: 'Hypotheses', value: hypotheses.length },
                { label: 'Evidence', value: evidence.length },
              ].map(row => (
                <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', fontSize: '0.8rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                  <span style={{ fontWeight: 600 }}>{row.value}</span>
                </div>
              ))}
            </motion.div>

            {/* Revision Narrative */}
            {revisionNarrative && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-card-static"
              >
                <div className="section-title">💡 Reasoning Update</div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{revisionNarrative}</p>
              </motion.div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="disclaimer-banner" style={{ margin: '0.75rem 0 0.5rem' }}>
          ⚠️ FOR MEDICAL EDUCATION ONLY — Not for clinical use • CuraBot v2.0 • 6 LLM-Powered Agents
        </div>
      </div>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            style={{
              position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 9999,
              background: 'rgba(239,68,68,0.15)', backdropFilter: 'blur(12px)',
              border: '1px solid rgba(239,68,68,0.25)', borderRadius: 'var(--radius-lg)',
              padding: '1rem 1.5rem', color: '#fecaca', maxWidth: 400, fontSize: '0.85rem',
            }}
          >
            ❌ {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ChatPage
