import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

export default function Landing() {
  const { user } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-zinc-100 flex flex-col transition-colors">
      {/* Navigation */}
      <header className="border-b border-gray-200 dark:border-zinc-800 px-6 py-4 flex items-center justify-between">
        <span className="font-semibold text-base tracking-tight text-gray-900 dark:text-white">
          Chat with PDF
        </span>
        <div className="flex items-center gap-3 text-sm">
          {/* Minimal Text-Only Theme Toggle - Strictly No Icons */}
          <button
            onClick={toggleTheme}
            className="border border-gray-300 dark:border-zinc-800 px-3 py-1 text-xs text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-900"
          >
            {theme === 'dark' ? 'Theme: Dark' : 'Theme: Light'}
          </button>

          {user ? (
            <>
              {user.role === 'admin' && (
                <Link to="/admin" className="text-blue-600 dark:text-blue-400">
                  Admin
                </Link>
              )}
              <Link
                to="/chat"
                className="bg-blue-600 text-white px-3 py-1.5 font-medium"
              >
                Go to Chat
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="border border-gray-300 dark:border-zinc-800 px-3 py-1.5 text-gray-800 dark:text-zinc-200"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="bg-blue-600 text-white px-3 py-1.5 font-medium"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-4xl mx-auto px-6 py-16 flex flex-col justify-center">
        <div className="mb-12">
          <p className="text-xs uppercase tracking-wider text-gray-500 dark:text-zinc-400 mb-2">
            RAG Powered Document Q&A
          </p>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-4 text-gray-900 dark:text-white">
            Chat with your PDF documents.
          </h1>
          <p className="text-gray-600 dark:text-zinc-300 text-base max-w-2xl mb-6">
            Upload an English PDF and ask questions. Answers are generated strictly
            from the document content using Google Gemini with exact source page
            citations.
          </p>

          <div className="flex flex-wrap gap-3">
            {user ? (
              <Link
                to="/chat"
                className="bg-blue-600 text-white px-5 py-2.5 text-sm font-medium"
              >
                Open Chat
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="bg-blue-600 text-white px-5 py-2.5 text-sm font-medium"
                >
                  Get started
                </Link>
                <Link
                  to="/login"
                  className="border border-gray-300 dark:border-zinc-800 text-gray-900 dark:text-zinc-100 px-5 py-2.5 text-sm font-medium"
                >
                  Sign in
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Notice Banner */}
        <div className="border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-950 p-4 mb-12 text-sm text-gray-700 dark:text-zinc-300">
          <span className="font-semibold text-gray-900 dark:text-white">Language scope:</span> This application is built strictly for English documents and English questions. If information is not in the document, it states that clearly without guessing.
        </div>

        {/* Features Grid - Minimal, No Icons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border border-gray-200 dark:border-zinc-800 p-5 bg-white dark:bg-zinc-950">
            <h3 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">
              1. Grounded Answers
            </h3>
            <p className="text-xs text-gray-600 dark:text-zinc-400 leading-relaxed">
              Gemini LLM uses only the retrieved context chunks from your uploaded PDF. It will never hallucinate or invent outside facts.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-zinc-800 p-5 bg-white dark:bg-zinc-950">
            <h3 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">
              2. Source Page Numbers
            </h3>
            <p className="text-xs text-gray-600 dark:text-zinc-400 leading-relaxed">
              Every single answer includes verified source page references extracted from the PDF vector chunks for quick verification.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-zinc-800 p-5 bg-white dark:bg-zinc-950">
            <h3 className="font-semibold text-sm mb-2 text-gray-900 dark:text-white">
              3. Tenant Isolation
            </h3>
            <p className="text-xs text-gray-600 dark:text-zinc-400 leading-relaxed">
              Your files and embeddings are strictly isolated by your user ID. Other users cannot access your documents or chat data.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-zinc-800 px-6 py-4 text-center text-xs text-gray-500 dark:text-zinc-500">
        English only. Built with React, Tailwind CSS, FastAPI, ChromaDB, and Google Gemini.
      </footer>
    </div>
  )
}
