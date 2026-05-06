import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/useAuthStore'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import ProfilePage from './pages/ProfilePage'
import AboutPage from './pages/AboutPage'
import './index.css'

function App() {
  const { loadUser, isAuthenticated } = useAuthStore()

  useEffect(() => {
    loadUser()
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/dashboard" element={
          isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />
        } />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/profile" element={
          isAuthenticated ? <ProfilePage /> : <Navigate to="/login" />
        } />
        <Route path="/about" element={<AboutPage />} />
        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  )
}

export default App