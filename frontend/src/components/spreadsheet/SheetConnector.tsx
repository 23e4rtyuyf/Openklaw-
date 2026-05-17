import { useState } from 'react'
import { Link2, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { sheetsApi } from '../../lib/api'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { extractSheetId } from '../../lib/utils'

interface SheetConnectorProps {
  onConnected: (headers: string[], rows: string[][], url: string) => void
}

export default function SheetConnector({ onConnected }: SheetConnectorProps) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)

  const connect = async () => {
    const id = extractSheetId(url)
    if (!id) { setError('Could not extract sheet ID from URL'); return }
    setLoading(true)
    setError('')
    try {
      const data = await sheetsApi.googlePreview(url)
      setConnected(true)
      onConnected(data.headers, data.rows, url)
    } catch (e: unknown) {
      setError((e as Error).message || 'Failed to connect')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1">
          <Input
            placeholder="https://docs.google.com/spreadsheets/d/..."
            value={url}
            onChange={e => { setUrl(e.target.value); setConnected(false); setError('') }}
            className="font-mono text-xs"
          />
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={connect}
          disabled={!url.trim() || loading}
          loading={loading}
        >
          <Link2 size={14} />
          Connect
        </Button>
      </div>

      {connected && (
        <div className="flex items-center gap-2 text-xs text-emerald-400">
          <CheckCircle2 size={13} />
          Connected successfully
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-xs text-red-400">
          <AlertCircle size={13} />
          {error}
        </div>
      )}

      <p className="text-xs text-gray-600">
        Requires service account with Viewer access to the sheet.
        Configure credentials in Settings → Google.
      </p>
    </div>
  )
}
