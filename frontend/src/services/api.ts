 
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ChatResponse {
  session_id: string
  hypotheses: Array<{
    name: string
    confidence: number
    supporting: number
    contradicting: number
    reasoning?: string
  }>
  suggested_questions: string[]
  evidence: Array<{
    finding: string
    supports: string[]
    contradicts: string[]
    confidence?: number
  }>
  bias_flags: Array<{
    bias: string
    description: string
    severity: 'low' | 'medium' | 'high'
  }>
  iteration: number
  need_more_info: boolean
  agent_thoughts: Array<{
    agent: string
    thought: string
    timestamp: string
    data?: any
  }>
  disclaimer: string
}

export const sendMessage = async (
  message: string,
  sessionId?: string
): Promise<ChatResponse> => {
  // Use relative path for Vite proxy or full URL from env
  const response = await api.post('/api/chat', { message, session_id: sessionId })
  return response.data
}

export const resetSession = async (sessionId: string): Promise<void> => {
  // Matches backend @app.post("/api/session/reset")
  await api.post('/api/session/reset', { session_id: sessionId })
}

export const getHealth = async (): Promise<any> => {
  const response = await api.get('/health')
  return response.data
}