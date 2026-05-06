import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/useAuthStore'
import { api } from '../services/api'

const ProfilePage: React.FC = () => {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const [profile, setProfile] = useState({
    full_name: '', age: '', gender: '', blood_group: '',
    known_conditions: '', medications: '', allergies: '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return }
    loadProfile()
  }, [isAuthenticated])

  const loadProfile = async () => {
    try {
      const res = await api.get('/api/auth/me', { headers: { 'x-user-id': user?.user_id || '' } })
      const p = res.data
      setProfile({
        full_name: p.full_name || '',
        age: p.age?.toString() || '',
        gender: p.gender || '',
        blood_group: p.blood_group || '',
        known_conditions: (p.known_conditions || []).join(', '),
        medications: (p.medications || []).join(', '),
        allergies: (p.allergies || []).join(', '),
      })
    } catch { /* silent */ }
  }

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      await api.put('/api/auth/profile', {
        full_name: profile.full_name || undefined,
        age: profile.age ? parseInt(profile.age) : undefined,
        gender: profile.gender || undefined,
        blood_group: profile.blood_group || undefined,
        known_conditions: profile.known_conditions ? profile.known_conditions.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        medications: profile.medications ? profile.medications.split(',').map(s => s.trim()).filter(Boolean) : undefined,
        allergies: profile.allergies ? profile.allergies.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      }, { headers: { 'x-user-id': user?.user_id || '' } })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch { /* silent */ }
    setSaving(false)
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <div className="cyber-background">
        <div className="gradient-orb orb-1" />
        <div className="gradient-orb orb-2" />
        <div className="grid-overlay" />
      </div>

      <div style={{ position: 'relative', zIndex: 5, maxWidth: 700, margin: '0 auto', padding: '2rem' }}>
        {/* Nav */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}
        >
          <button className="btn-ghost" onClick={() => navigate('/dashboard')}>← Dashboard</button>
          <span className="badge badge-medical">Patient Profile</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card-static"
          style={{ padding: '2.5rem' }}
        >
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.5rem', marginBottom: '0.5rem' }}>
            👤 Medical Profile
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '2rem' }}>
            This information helps CuraBot provide context-aware diagnosis for returning users.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Full Name</label>
                <input className="glass-input" value={profile.full_name} onChange={e => setProfile({ ...profile, full_name: e.target.value })} />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Age</label>
                <input className="glass-input" type="number" value={profile.age} onChange={e => setProfile({ ...profile, age: e.target.value })} />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Gender</label>
                <select className="glass-input" value={profile.gender} onChange={e => setProfile({ ...profile, gender: e.target.value })}>
                  <option value="">Select</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Blood Group</label>
                <select className="glass-input" value={profile.blood_group} onChange={e => setProfile({ ...profile, blood_group: e.target.value })}>
                  <option value="">Select</option>
                  {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Known Medical Conditions <span style={{ color: 'var(--text-muted)' }}>(comma separated)</span></label>
              <input className="glass-input" placeholder="e.g. Hypertension, Diabetes, Asthma" value={profile.known_conditions} onChange={e => setProfile({ ...profile, known_conditions: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Current Medications <span style={{ color: 'var(--text-muted)' }}>(comma separated)</span></label>
              <input className="glass-input" placeholder="e.g. Metformin, Amlodipine" value={profile.medications} onChange={e => setProfile({ ...profile, medications: e.target.value })} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>Allergies <span style={{ color: 'var(--text-muted)' }}>(comma separated)</span></label>
              <input className="glass-input" placeholder="e.g. Penicillin, Sulfa drugs" value={profile.allergies} onChange={e => setProfile({ ...profile, allergies: e.target.value })} />
            </div>

            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginTop: '0.5rem' }}>
              <button className="btn-primary" onClick={handleSave} disabled={saving}
                style={{ padding: '0.75rem 2rem' }}>
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
              {saved && <span style={{ color: 'var(--color-emerald)', fontSize: '0.85rem' }}>✓ Saved successfully</span>}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default ProfilePage
