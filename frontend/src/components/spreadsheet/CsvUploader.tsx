import { useCallback, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import Papa from 'papaparse'
import { cn, formatBytes } from '../../lib/utils'

interface CsvUploaderProps {
  onParsed: (filename: string, headers: string[], rows: string[][]) => void
  onFileUpload?: (file: File) => void
}

export default function CsvUploader({ onParsed, onFileUpload }: CsvUploaderProps) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  const processFile = useCallback((f: File) => {
    setFile(f)
    setError('')
    onFileUpload?.(f)

    if (f.name.endsWith('.csv') || f.type === 'text/csv') {
      Papa.parse<string[]>(f, {
        complete: (result) => {
          const all = result.data.filter(r => r.some(c => c !== ''))
          if (all.length < 2) { setError('CSV appears empty'); return }
          onParsed(f.name, all[0], all.slice(1))
        },
        error: () => setError('Failed to parse CSV'),
      })
    }
    // .xlsx handled server-side via upload endpoint
  }, [onParsed, onFileUpload])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) processFile(f)
  }, [processFile])

  return (
    <div className="space-y-2">
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer',
          dragging ? 'border-sky-500/60 bg-sky-500/5' : 'border-[#1f2937] hover:border-[#374151] bg-[#0d1117]'
        )}
        onClick={() => document.getElementById('csv-file-input')?.click()}
      >
        <input
          id="csv-file-input"
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) processFile(f) }}
        />

        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText size={20} className="text-sky-400" />
            <div className="text-left">
              <p className="text-sm font-medium text-gray-200">{file.name}</p>
              <p className="text-xs text-gray-500">{formatBytes(file.size)}</p>
            </div>
            <button
              onClick={e => { e.stopPropagation(); setFile(null) }}
              className="ml-2 text-gray-500 hover:text-gray-300"
            >
              <X size={14} />
            </button>
          </div>
        ) : (
          <>
            <Upload size={24} className="mx-auto mb-3 text-gray-500" />
            <p className="text-sm text-gray-400 mb-1">Drop CSV or Excel file here</p>
            <p className="text-xs text-gray-600">or click to browse · .csv, .xlsx, .xls</p>
          </>
        )}
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}
