import { createContext, useContext, useEffect, useState } from 'react'
import api, { setAccessToken, getAccessToken } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function init() {
      try {
        const refreshRes = await api.post('/api/auth/refresh')
        const token = refreshRes.data.access_token
        setAccessToken(token)
        const meRes = await api.get('/api/auth/me')
        setUser(meRes.data)
      } catch {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  useEffect(() => {
    function handleAuthLogout() {
      logout()
    }
    window.addEventListener('auth:logout', handleAuthLogout)
    return () => window.removeEventListener('auth:logout', handleAuthLogout)
  }, [])

  function login(token, userData) {
    setAccessToken(token)
    setUser(userData)
  }

  async function logout() {
    try {
      await api.post('/api/auth/logout')
    } catch {
      // ignore
    }
    setAccessToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, accessToken: getAccessToken(), loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
