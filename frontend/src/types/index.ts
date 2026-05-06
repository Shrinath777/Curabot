// Agent Types
export interface Agent {
  id: string
  name: string
  description: string
  status: 'idle' | 'processing' | 'completed' | 'error'
}

export interface AgentThought {
  agentId: string
  agentName: string
  thought: string
  timestamp: Date
  data?: any
}

// Hypothesis Types
export interface Hypothesis {
  name: string
  confidence: number
  supporting: number
  contradicting: number
  reasoning?: string
  evidenceIds?: string[]
}

// Evidence Types
export interface Evidence {
  id: string
  finding: string
  findingType: 'symptom' | 'vital' | 'lab' | 'risk_factor'
  supports: string[]
  contradicts: string[]
  confidence: number
  timestamp: Date
}

// Bias Types
export interface BiasFlag {
  bias: 'anchoring' | 'confirmation_bias' | 'premature_closure' | 'availability_bias'
  description: string
  severity: 'low' | 'medium' | 'high'
  mitigation?: string
}

// Chat Types
export interface ChatMessage {
  id: string
  text: string
  sender: 'user' | 'bot'
  timestamp: Date
  metadata?: {
    hypotheses?: Hypothesis[]
    evidence?: Evidence[]
  }
}

// Session Types
export interface Session {
  id: string
  createdAt: Date
  lastUpdated: Date
  messages: ChatMessage[]
  hypotheses: Hypothesis[]
  evidence: Evidence[]
  biasFlags: BiasFlag[]
  stage: number
  iteration: number
}

// API Response Types
export interface ChatResponse {
  session_id: string
  hypotheses: Hypothesis[]
  evidence: Evidence[]
  suggested_questions: string[]
  bias_flags: BiasFlag[]
  iteration: number
  need_more_info: boolean
  agent_thoughts: AgentThought[]
  disclaimer: string
}

// Store Types
export interface DiagnosticState {
  sessionId: string | null
  hypotheses: Hypothesis[]
  evidence: Evidence[]
  suggestions: string[]
  biasFlags: BiasFlag[]
  iteration: number
  loading: boolean
  error: string | null
  agentThoughts: AgentThought[]
}

export interface AgentStoreState {
  agentStates: Record<string, {
    status: 'idle' | 'processing' | 'done' | 'error'
    currentThought?: string
    lastUpdate?: Date
  }>
}

// UI Types
export interface Theme {
  mode: 'light' | 'dark' | 'system'
  accent: 'primary' | 'secondary' | 'accent'
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  message: string
  duration?: number
}

// Utility Types
export type Severity = 'low' | 'medium' | 'high'
export type FindingType = 'symptom' | 'vital' | 'lab' | 'risk_factor'
export type AgentStatus = 'idle' | 'processing' | 'completed' | 'error'