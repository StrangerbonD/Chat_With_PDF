import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Admin() {
  const { user } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)
  const PAGE_SIZE = 20

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await api.get('/api/admin/stats')
        setStats(res.data)
      } catch {
        // ignore
      }
    }
    fetchStats()
  }, [])

  const fetchUsers = useCallback(async (searchVal, pageVal) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/api/admin/users', {
        params: { search: searchVal, page: pageVal, page_size: PAGE_SIZE },
      })
      setUsers(res.data.users || res.data.items || res.data)
      const total = res.data.total || res.data.total_count || 0
      setTotalPages(Math.max(1, Math.ceil(total / PAGE_SIZE)))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUsers(search, page)
  }, [page, fetchUsers])

  function handleSearchChange(e) {
    const val = e.target.value
    setSearch(val)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setPage(1)
      fetchUsers(val, 1)
    }, 300)
  }

  async function patchUser(userId, data) {
    try {
      await api.patch(`/api/admin/users/${userId}`, data)
      fetchUsers(search, page)
    } catch (err) {
      setError(err.response?.data?.detail || 'Action failed.')
    }
  }

  async function deleteUser(userId) {
    if (!window.confirm('Delete this user?')) return
    try {
      await api.delete(`/api/admin/users/${userId}`)
      fetchUsers(search, page)
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed.')
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 p-6 transition-colors">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">Admin Panel</h1>
          <Link to="/chat" className="text-sm text-blue-600 dark:text-blue-400">
            Back to Chat
          </Link>
        </div>
        <button
          onClick={toggleTheme}
          className="border border-gray-300 dark:border-zinc-800 px-3 py-1 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
        >
          {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            ['Total users', stats.total_users],
            ['Verified', stats.verified_users],
            ['Active', stats.active_users],
            ['Documents', stats.total_documents],
          ].map(([label, val]) => (
            <div key={label} className="border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-3">
              <p className="text-xs text-gray-500 dark:text-zinc-400">{label}</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{val ?? '—'}</p>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-red-600 dark:text-red-400 text-sm mb-3">{error}</p>}

      {/* Search */}
      <input
        type="text"
        value={search}
        onChange={handleSearchChange}
        placeholder="Search users"
        className="border border-gray-300 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-gray-900 dark:text-white px-3 py-2 text-sm mb-4 w-full max-w-xs focus:outline-none focus:border-blue-600"
      />

      {/* Table */}
      {loading ? (
        <p className="text-sm text-gray-500 dark:text-zinc-400">Loading...</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-zinc-800 text-gray-700 dark:text-zinc-300">
                <th className="text-left py-2 pr-4 font-medium">Email</th>
                <th className="text-left py-2 pr-4 font-medium">Name</th>
                <th className="text-left py-2 pr-4 font-medium">Role</th>
                <th className="text-left py-2 pr-4 font-medium">Active</th>
                <th className="text-left py-2 pr-4 font-medium">Verified</th>
                <th className="text-left py-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === user?.id || u.email === user?.email
                return (
                  <tr key={u.id} className="border-b border-gray-100 dark:border-zinc-900">
                    <td className="py-2 pr-4 text-gray-900 dark:text-zinc-100">{u.email}</td>
                    <td className="py-2 pr-4 text-gray-900 dark:text-zinc-100">{u.full_name}</td>
                    <td className="py-2 pr-4 text-gray-900 dark:text-zinc-100">{u.role}</td>
                    <td className="py-2 pr-4 text-gray-900 dark:text-zinc-100">{u.is_active ? 'Yes' : 'No'}</td>
                    <td className="py-2 pr-4 text-gray-900 dark:text-zinc-100">{u.is_verified ? 'Yes' : 'No'}</td>
                    <td className="py-2 flex gap-2 flex-wrap">
                      {!isSelf && (
                        <>
                          <button
                            onClick={() => patchUser(u.id, { is_active: !u.is_active })}
                            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-gray-800 dark:text-zinc-200 hover:bg-gray-50 dark:hover:bg-zinc-900"
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => patchUser(u.id, { role: u.role === 'admin' ? 'user' : 'admin' })}
                            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-gray-800 dark:text-zinc-200 hover:bg-gray-50 dark:hover:bg-zinc-900"
                          >
                            {u.role === 'admin' ? 'Make user' : 'Make admin'}
                          </button>
                          <button
                            onClick={() => deleteUser(u.id)}
                            className="border border-gray-300 dark:border-zinc-800 px-2 py-0.5 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                )
              })}
              {users.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-4 text-gray-500 dark:text-zinc-500">No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center gap-3 mt-4 text-sm">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="border border-gray-300 dark:border-zinc-800 px-3 py-1 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-zinc-900"
        >
          Prev
        </button>
        <span className="text-gray-700 dark:text-zinc-300">Page {page} of {totalPages}</span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="border border-gray-300 dark:border-zinc-800 px-3 py-1 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-zinc-900"
        >
          Next
        </button>
      </div>
    </div>
  )
}
