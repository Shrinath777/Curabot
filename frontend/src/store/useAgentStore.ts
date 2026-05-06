 
import { create } from 'zustand'

interface AgentState {
  agentStates: Record<string, {
    status: 'idle' | 'processing' | 'done' | 'error'
    currentThought?: string
    lastUpdate?: Date
  }>
  updateAgentState: (agentId: string, state: Partial<AgentState['agentStates'][string]>) => void
  resetAgents: () => void
}

export const useAgentStore = create<AgentState>((set) => ({
  agentStates: {
    normalizer: { status: 'idle' },
    generator: { status: 'idle' },
    evaluator: { status: 'idle' },
    reviser: { status: 'idle' },
    strategist: { status: 'idle' },
    critique: { status: 'idle' }
  },

  updateAgentState: (agentId, state) => {
    set((prev) => ({
      agentStates: {
        ...prev.agentStates,
        [agentId]: {
          ...prev.agentStates[agentId],
          ...state,
          lastUpdate: new Date()
        }
      }
    }))
  },

  resetAgents: () => {
    set({
      agentStates: {
        normalizer: { status: 'idle' },
        generator: { status: 'idle' },
        evaluator: { status: 'idle' },
        reviser: { status: 'idle' },
        strategist: { status: 'idle' },
        critique: { status: 'idle' }
      }
    })
  }
}))