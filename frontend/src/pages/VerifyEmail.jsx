import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../services/api'
import { useTheme } from '../context/ThemeContext'

export default function VerifyEmail() {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()
  const [email, setEmail] = useState(location.state?.email || '')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendMsg, setResendMsg] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/verify-email', { email, code })
      navigate('/login')
    } catch (err) {
      setError(err.response?.data?.detail || 'Verification failed.')
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    setError('')
    setResendMsg('')
    try {
      await api.post('/api/auth/resend-code', { email })
      setResendMsg('Code resent.')
    } catch (err) {
      if (err.response?.status === 429) {
        setError('Too many requests. Please wait before resending.')
      } else {
        setError(err.response?.data?.detail || 'Resend failed.')
      }
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 flex items-center justify-center p-4 transition-colors">
      <div className="w-full max-w-sm border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Verify Email</h1>
          <button
            type="button"
            onClick={toggleTheme}
            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
          >
            {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
          </button>
        </div>

        {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3">{error}</p>}
        {resendMsg && <p className="text-green-600 dark:text-green-400 text-sm mb-3">{resendMsg}</p>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-black text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
          />
          <input
            type="text"
            placeholder="6-digit code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            maxLength={6}
            required
            className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-black text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 text-sm disabled:opacity-50 font-medium"
          >
            {loading ? 'Loading...' : 'Verify'}
          </button>
        </form>

        <button
          onClick={handleResend}
          className="mt-4 text-sm text-blue-600 dark:text-blue-400"
        >
          Resend code
        </button>
      </div>
    </div>
  )
}
