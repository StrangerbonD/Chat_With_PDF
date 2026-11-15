import { useState } from 'react'

export default function ChatInput({ onSend, disabled, sending }) {
  const [question, setQuestion] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || disabled || sending) return
    onSend(trimmed)
    setQuestion('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-200 dark:border-zinc-800 p-3 flex gap-2 bg-white dark:bg-black"
    >
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder={disabled ? 'Upload a PDF first' : 'Ask a question...'}
        disabled={disabled || sending}
        className="flex-1 border border-gray-300 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-gray-900 dark:text-white px-3 py-2 text-sm disabled:bg-gray-50 dark:disabled:bg-zinc-900 placeholder:text-gray-400 dark:placeholder:text-zinc-600 focus:outline-none focus:border-blue-600"
      />
      <button
        type="submit"
        disabled={disabled || sending || !question.trim()}
        className="bg-blue-600 text-white px-4 py-2 text-sm disabled:opacity-50 font-medium"
      >
        Send
      </button>
    </form>
  )
}
