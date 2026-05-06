import { api } from './api'

export interface AgentState {
  id: string
  name: string
  status: 'idle' | 'processing' | 'completed' | 'error'
  output?: any
  error?: string
}

export interface OrchestrationResult {
  sessionId: string
  agents: AgentState[]
  finalHypotheses: any[]
  evidence: any[]
  suggestions: string[]
}

class AgentOrchestrator {
  private agents = [
    { id: 'normalizer', name: 'Symptom Normalizer' },
    { id: 'generator', name: 'Hypothesis Generator' },
    { id: 'evaluator', name: 'Evidence Evaluator' },
    { id: 'reviser', name: 'Hypothesis Reviser' },
    { id: 'strategist', name: 'Diagnostic Strategist' },
    { id: 'critique', name: 'Self Critique' }
  ]

  async runFullPipeline(
    sessionId: string,
    symptoms: string[]
  ): Promise<OrchestrationResult> {
    const agentStates: AgentState[] = this.agents.map(a => ({
      ...a,
      status: 'idle'
    }))

    try {
      // Step 1: Symptom Normalizer
      agentStates[0].status = 'processing'
      const normalized = await api.post('/agent/normalizer', {
        session_id: sessionId,
        symptoms
      })
      agentStates[0].status = 'completed'
      agentStates[0].output = normalized.data

      // Step 2: Hypothesis Generator
      agentStates[1].status = 'processing'
      const hypotheses = await api.post('/agent/generator', {
        session_id: sessionId,
        normalized_symptoms: normalized.data
      })
      agentStates[1].status = 'completed'
      agentStates[1].output = hypotheses.data

      // Step 3: Evidence Evaluator
      agentStates[2].status = 'processing'
      const evidence = await api.post('/agent/evaluator', {
        session_id: sessionId,
        hypotheses: hypotheses.data,
        normalized_symptoms: normalized.data
      })
      agentStates[2].status = 'completed'
      agentStates[2].output = evidence.data

      // Step 4: Hypothesis Reviser
      agentStates[3].status = 'processing'
      const revised = await api.post('/agent/reviser', {
        session_id: sessionId,
        hypotheses: hypotheses.data,
        evidence: evidence.data
      })
      agentStates[3].status = 'completed'
      agentStates[3].output = revised.data

      // Step 5: Diagnostic Strategist
      agentStates[4].status = 'processing'
      const strategy = await api.post('/agent/strategist', {
        session_id: sessionId,
        hypotheses: revised.data
      })
      agentStates[4].status = 'completed'
      agentStates[4].output = strategy.data

      // Step 6: Self Critique
      agentStates[5].status = 'processing'
      const critique = await api.post('/agent/critique', {
        session_id: sessionId,
        hypotheses: revised.data,
        evidence: evidence.data
      })
      agentStates[5].status = 'completed'
      agentStates[5].output = critique.data

      return {
        sessionId,
        agents: agentStates,
        finalHypotheses: revised.data,
        evidence: evidence.data,
        suggestions: strategy.data.suggestions
      }
    } catch (error) {
      console.error('Pipeline error:', error)
      throw error
    }
  }

  async runSingleAgent(
    sessionId: string,
    agentId: string,
    input: any
  ): Promise<any> {
    try {
      const response = await api.post(`/agent/${agentId}`, {
        session_id: sessionId,
        ...input
      })
      return response.data
    } catch (error) {
      console.error(`Agent ${agentId} error:`, error)
      throw error
    }
  }
}

export const agentOrchestrator = new AgentOrchestrator()