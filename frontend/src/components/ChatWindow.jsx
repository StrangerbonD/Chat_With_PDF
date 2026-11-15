import { useEffect, useRef } from 'react'

export default function ChatWindow({ messages, sending, error, hasDocument }) {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  return (
    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-white dark:bg-black">
      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}

      {messages.length === 0 && !sending && (
        <p className="text-gray-400 dark:text-zinc-600 text-sm">
          {hasDocument ? 'Ask a question.' : 'Upload a PDF first.'}
        </p>
      )}

      {messages.map((msg, i) => (
        <div
          key={i}
          className={`max-w-xl ${
            msg.role === 'user' ? 'self-end' : 'self-start'
          }`}
        >
          <div
            className={`px-3 py-2 text-sm border ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white dark:bg-zinc-950 text-gray-900 dark:text-zinc-100 border-gray-200 dark:border-zinc-800'
            }`}
          >
            {msg.content}
          </div>
          {msg.role === 'assistant' &&
            msg.source_pages &&
            msg.source_pages.length > 0 && (
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                Pages: {msg.source_pages.join(', ')}
              </p>
            )}
        </div>
      ))}

      {sending && (
        <div className="self-start px-3 py-2 text-sm border border-gray-200 dark:border-zinc-800 text-gray-500 dark:text-zinc-400 bg-white dark:bg-zinc-950">
          Loading...
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
