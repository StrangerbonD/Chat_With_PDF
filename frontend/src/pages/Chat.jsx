import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import PdfUploader from '../components/PdfUploader'
import ChatWindow from '../components/ChatWindow'
import ChatInput from '../components/ChatInput'

export default function Chat() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [document, setDocument] = useState(null)
  const [messages, setMessages] = useState([])
  const [uploading, setUploading] = useState(false)
  const [sending, setSending] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [chatError, setChatError] = useState('')

  // Load most recent document on mount
  useEffect(() => {
    async function fetchDocuments() {
      try {
        const res = await api.get('/api/documents')
        const docs = res.data
        if (docs && docs.length > 0) {
          const sorted = [...docs].sort(
            (a, b) => new Date(b.created_at) - new Date(a.created_at)
          )
          const docId = sorted[0].id || sorted[0].document_id
          setDocument({
            id: docId,
            document_id: docId,
            filename: sorted[0].filename,
            total_pages: sorted[0].total_pages,
          })
        }
      } catch {
        // ignore
      }
    }
    fetchDocuments()
  }, [])

  // Load chat history from localStorage whenever the active document changes
  useEffect(() => {
    const docId = document?.id || document?.document_id
    if (docId) {
      try {
        const saved = localStorage.getItem(`chat_history_${docId}`)
        if (saved) {
          setMessages(JSON.parse(saved))
        } else {
          setMessages([])
        }
      } catch {
        setMessages([])
      }
    } else {
      setMessages([])
    }
  }, [document?.id, document?.document_id])

  // Persist messages to localStorage whenever messages update
  useEffect(() => {
    const docId = document?.id || document?.document_id
    if (docId && messages.length > 0) {
      try {
        localStorage.setItem(`chat_history_${docId}`, JSON.stringify(messages))
      } catch {
        // ignore
      }
    }
  }, [messages, document?.id, document?.document_id])

  async function handleUpload(file) {
    setUploadError('')
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/api/documents/upload', formData)
      const docId = res.data.id || res.data.document_id
      setDocument({
        id: docId,
        document_id: docId,
        filename: res.data.filename,
        total_pages: res.data.total_pages,
      })
      setMessages([])
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete() {
    const docId = document?.id || document?.document_id
    if (!docId) return
    if (!window.confirm('Delete this document?')) return
    setUploadError('')
    try {
      await api.delete(`/api/documents/${docId}`)
      localStorage.removeItem(`chat_history_${docId}`)
      setDocument(null)
      setMessages([])
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Delete failed.')
    }
  }

  async function handleSend(q) {
    const docId = document?.id || document?.document_id
    if (!docId) return
    setMessages((prev) => [...prev, { role: 'user', content: q, source_pages: [] }])
    setSending(true)
    setChatError('')
    try {
      const res = await api.post('/api/chat', {
        document_id: docId,
        question: q,
      })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.answer,
          source_pages: res.data.source_pages || [],
        },
      ])
    } catch (err) {
      setChatError(err.response?.data?.detail || 'Chat failed.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col md:flex-row h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 transition-colors">
      {/* Sidebar */}
      <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-gray-200 dark:border-zinc-800 p-4 shrink-0 bg-white dark:bg-black">
        <PdfUploader
          document={document}
          uploading={uploading}
          error={uploadError}
          onUpload={handleUpload}
          onDelete={handleDelete}
        />
      </div>

      {/* Main */}
      <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-black">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-zinc-800 px-4 py-3 flex items-center justify-between shrink-0 bg-white dark:bg-black">
          <Link to="/" className="font-semibold text-sm hover:text-blue-600 dark:hover:text-blue-400">
            Chat with PDF
          </Link>
          <div className="flex items-center gap-3">
            {/* Minimal Theme Toggle - Plain text only, no icons */}
            <button
              onClick={toggleTheme}
              className="border border-gray-300 dark:border-zinc-800 px-3 py-1 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
            >
              {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
            </button>

            {user?.role === 'admin' && (
              <Link to="/admin" className="text-blue-600 dark:text-blue-400 text-sm">
                Admin
              </Link>
            )}
            <button
              onClick={logout}
              className="border border-gray-300 dark:border-zinc-800 px-3 py-1 text-sm text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Messages */}
        <ChatWindow
          messages={messages}
          sending={sending}
          error={chatError}
          hasDocument={Boolean(document)}
        />

        {/* Input */}
        <ChatInput
          onSend={handleSend}
          disabled={!document}
          sending={sending}
        />
      </div>
    </div>
  )
}
