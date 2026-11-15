import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useTheme } from '../context/ThemeContext'

export default function ForgotPassword() {
  const { theme, toggleTheme } = useTheme()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/api/auth/forgot-password', { email })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Request failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 flex items-center justify-center p-4 transition-colors">
      <div className="w-full max-w-sm border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Forgot Password</h1>
          <button
            type="button"
            onClick={toggleTheme}
            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
          >
            {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
          </button>
        </div>

        {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3">{error}</p>}
        {success ? (
          <p className="text-green-600 dark:text-green-400 text-sm">
            Code sent.{' '}
            <Link to="/reset-password" className="text-blue-600 dark:text-blue-400">
              Reset password
            </Link>
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-black text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 text-sm disabled:opacity-50 font-medium"
            >
              {loading ? 'Loading...' : 'Send code'}
            </button>
          </form>
        )}
        <div className="flex gap-3 mt-4 text-sm">
          <Link to="/reset-password" className="text-blue-600 dark:text-blue-400">
            Reset password
          </Link>
          <Link to="/login" className="text-blue-600 dark:text-blue-400">
            Login
          </Link>
        </div>
      </div>
    </div>
  )
}
