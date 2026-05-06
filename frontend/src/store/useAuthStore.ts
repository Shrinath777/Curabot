import { create } from 'zustand'
import { api } from '../services/api'

interface User {
  user_id: string
  email: string
  full_name?: string
  access_token?: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<boolean>
  signup: (email: string, password: string, fullName: string) => Promise<boolean>
  logout: () => void
  loadUser: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post('/api/auth/login', { email, password })
      const user = response.data
      if (user.status === 'success') {
        localStorage.setItem('curabot_user', JSON.stringify(user))
        set({ user, isAuthenticated: true, loading: false })
        return true
      } else {
        set({ error: user.error || 'Login failed', loading: false })
        return false
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Login failed'
      set({ error: msg, loading: false })
      return false
    }
  },

  signup: async (email: string, password: string, fullName: string) => {
    set({ loading: true, error: null })
    try {
      const response = await api.post('/api/auth/signup', {
        email,
        password,
        full_name: fullName,
      })
      const data = response.data
      if (data.status === 'success') {
        // Auto-login after signup
        return await get().login(email, password)
      } else {
        set({ error: data.error || 'Signup failed', loading: false })
        return false
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Signup failed'
      set({ error: msg, loading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('curabot_user')
    set({ user: null, isAuthenticated: false })
  },

  loadUser: () => {
    const stored = localStorage.getItem('curabot_user')
    if (stored) {
      try {
        const user = JSON.parse(stored)
        set({ user, isAuthenticated: true })
      } catch {
        localStorage.removeItem('curabot_user')
      }
    }
  },
}))
