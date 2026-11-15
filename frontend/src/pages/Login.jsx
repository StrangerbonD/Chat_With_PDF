import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.post('/api/auth/login', form)
      const token = res.data.access_token
      const meRes = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      login(token, meRes.data)
      navigate('/chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 flex items-center justify-center p-4 transition-colors">
      <div className="w-full max-w-sm border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Login</h1>
          <button
            type="button"
            onClick={toggleTheme}
            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
          >
            {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
          </button>
        </div>

        {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3">{error}</p>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange}
            required
            className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-black text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
          />
          <input
            name="password"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
            className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-black text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:border-blue-600"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 text-sm disabled:opacity-50 font-medium"
          >
            {loading ? 'Loading...' : 'Login'}
          </button>
        </form>

        <div className="flex gap-3 mt-4 text-sm">
          <Link to="/register" className="text-blue-600 dark:text-blue-400">
            Register
          </Link>
          <Link to="/forgot-password" className="text-blue-600 dark:text-blue-400">
            Forgot password
          </Link>
        </div>
      </div>
    </div>
  )
}
