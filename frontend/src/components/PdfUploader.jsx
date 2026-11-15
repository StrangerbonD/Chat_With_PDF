import { useRef } from 'react'

export default function PdfUploader({
  document,
  uploading,
  error,
  onUpload,
  onDelete,
}) {
  const fileInputRef = useRef(null)

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      onUpload(file)
    }
    e.target.value = ''
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm font-medium truncate text-gray-900 dark:text-white">
        {document ? document.filename : 'No document'}
      </p>

      {error && <p className="text-red-600 dark:text-red-400 text-xs">{error}</p>}

      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        className="border border-gray-300 dark:border-zinc-800 text-gray-800 dark:text-zinc-200 px-3 py-1.5 text-sm disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-zinc-900"
      >
        {uploading ? 'Loading...' : 'Upload'}
      </button>

      {document && (
        <button
          type="button"
          onClick={onDelete}
          className="border border-gray-300 dark:border-zinc-800 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
        >
          Delete
        </button>
      )}
    </div>
  )
}
