 
import { io, Socket } from 'socket.io-client'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

class WebSocketService {
  private socket: Socket | null = null

  connect(sessionId: string, onMessage: (data: any) => void) {
    this.socket = io(WS_URL, {
      query: { sessionId },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
    })

    this.socket.on('agent_thought', (data) => {
      onMessage({ type: 'agent_thought', data })
    })

    this.socket.on('final', (data) => {
      onMessage({ type: 'final', data })
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })
  }

  sendMessage(message: string) {
    if (this.socket) {
      this.socket.send(JSON.stringify({ message }))
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
}

export const wsService = new WebSocketService()