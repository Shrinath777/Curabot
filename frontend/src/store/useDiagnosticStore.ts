import { create } from 'zustand'
import { api } from '../services/api'

interface Hypothesis {
  name: string
  confidence: number
  supporting: number
  contradicting: number
  reasoning?: string
  status?: string
}

interface Evidence {
  finding: string
  supports: string[]
  contradicts: string[]
  confidence?: number
}

interface BiasFlag {
  type: string
  bias: string
  description: string
  severity: 'low' | 'medium' | 'high'
  mitigation?: string
}

interface AgentThought {
  agent: string
  thought: string
  timestamp: string
  status?: string
}

interface ConfidenceSnapshot {
  iteration: number
  hypotheses: Array<{ name: string; confidence: number; iteration: number }>
  timestamp: string
}

interface DiagnosticState {
  sessionId: string | null
  hypotheses: Hypothesis[]
  evidence: Evidence[]
  suggestions: string[]
  biasFlags: BiasFlag[]
  agentThoughts: AgentThought[]
  loading: boolean
  error: string | null
  iteration: number
  needMoreInfo: boolean
  requestVitals: boolean
  vitalsNeeded: string[]
  confidenceTrajectory: ConfidenceSnapshot[]
  revisionNarrative: string
  shouldConclude: boolean
  conclusionMessage: string
  finalRecommendations: string[]
  sendMessage: (message: string, userId?: string, vitals?: any) => Promise<string>
  resetSession: () => void
}

export const useDiagnosticStore = create<DiagnosticState>((set, get) => ({
  sessionId: null,
  hypotheses: [],
  evidence: [],
  suggestions: [],
  biasFlags: [],
  agentThoughts: [],
  loading: false,
  error: null,
  iteration: 0,
  needMoreInfo: true,
  requestVitals: false,
  vitalsNeeded: [],
  confidenceTrajectory: [],
  revisionNarrative: '',
  shouldConclude: false,
  conclusionMessage: '',
  finalRecommendations: [],

  sendMessage: async (message: string, userId?: string, vitals?: any) => {
    set({ loading: true, error: null })
    try {
      const payload: any = {
        message,
        session_id: get().sessionId,
      }
      if (userId) payload.user_id = userId
      if (vitals) payload.vitals = vitals

      const response = await api.post('/api/chat', payload)
      const data = response.data

      set({
        sessionId: data.session_id,
        hypotheses: data.hypotheses || [],
        evidence: data.evidence || [],
        suggestions: data.questions || [],
        biasFlags: data.bias_flags || [],
        agentThoughts: data.agent_thoughts || [],
        iteration: data.iteration || 0,
        needMoreInfo: data.need_more_info ?? true,
        requestVitals: data.request_vitals || false,
        vitalsNeeded: data.vitals_needed || [],
        confidenceTrajectory: data.confidence_trajectory || [],
        revisionNarrative: data.revision_narrative || '',
        shouldConclude: data.should_conclude || false,
        conclusionMessage: data.conclusion_message || '',
        finalRecommendations: data.final_recommendations || [],
        loading: false,
      })

      return data.message || ''
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to send message'
      set({ error: msg, loading: false })
      return ''
    }
  },

  resetSession: () => {
    const sid = get().sessionId
    if (sid) {
      api.post(`/api/session/reset?session_id=${sid}`).catch(() => {})
    }
    set({
      sessionId: null,
      hypotheses: [],
      evidence: [],
      suggestions: [],
      biasFlags: [],
      agentThoughts: [],
      iteration: 0,
      needMoreInfo: true,
      requestVitals: false,
      vitalsNeeded: [],
      confidenceTrajectory: [],
      revisionNarrative: '',
      shouldConclude: false,
      conclusionMessage: '',
      finalRecommendations: [],
      error: null,
    })
  },
}))