import { useState, useEffect, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Settings as SettingsIcon, Mail, MessageSquare, Github, Database, Cloud,
  CheckCircle2, XCircle, ChevronDown, ChevronRight, Key, LogIn, LogOut,
} from 'lucide-react'
import { Input, Textarea } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

interface Integration {
  id: string
  name: string
  icon: ReactNode
  fields: { key: string; label: string; placeholder: string; type?: string; textarea?: boolean }[]
}

const INTEGRATIONS: Integration[] = [
  {
    id: 'openai',
    name: 'AI Provider (OpenAI / Anthropic)',
    icon: <Key size={15} className="text-violet-400" />,
    fields: [
      { key: 'OPENAI_API_KEY', label: 'OpenAI API Key', placeholder: 'sk-...' },
      { key: 'ANTHROPIC_API_KEY', label: 'Anthropic API Key', placeholder: 'sk-ant-... (set in Replit Secrets)' },
      { key: 'AI_MODEL', label: 'Model override', placeholder: 'claude-3-5-haiku-20241022' },
    ],
  },
  {
    id: 'gmail',
    name: 'Gmail (SMTP app password)',
    icon: <Mail size={15} className="text-red-400" />,
    fields: [
      { key: 'GMAIL_EMAIL', label: 'Gmail Address', placeholder: 'you@gmail.com' },
      { key: 'GMAIL_APP_PASSWORD', label: 'App Password', placeholder: 'xxxx xxxx xxxx xxxx', type: 'password' },
    ],
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: <MessageSquare size={15} className="text-orange-400" />,
    fields: [
      { key: 'SLACK_BOT_TOKEN', label: 'Bot Token', placeholder: 'xoxb-...' },
      { key: 'SLACK_SIGNING_SECRET', label: 'Signing Secret', placeholder: '...' },
    ],
  },
  {
    id: 'github',
    name: 'GitHub',
    icon: <Github size={15} className="text-gray-300" />,
    fields: [
      { key: 'GITHUB_TOKEN', label: 'Personal Access Token', placeholder: 'ghp_...' },
    ],
  },
  {
    id: 'notion',
    name: 'Notion',
    icon: <Database size={15} className="text-gray-200" />,
    fields: [
      { key: 'NOTION_TOKEN', label: 'Integration Token', placeholder: 'secret_...' },
    ],
  },
  {
    id: 'airtable',
    name: 'Airtable',
    icon: <Database size={15} className="text-emerald-400" />,
    fields: [
      { key: 'AIRTABLE_API_KEY', label: 'API Key', placeholder: 'pat...' },
      { key: 'AIRTABLE_BASE_ID', label: 'Base ID', placeholder: 'app...' },
    ],
  },
  {
    id: 'twilio',
    name: 'Twilio (SMS / WhatsApp)',
    icon: <MessageSquare size={15} className="text-red-300" />,
    fields: [
      { key: 'TWILIO_ACCOUNT_SID', label: 'Account SID', placeholder: 'AC...' },
      { key: 'TWILIO_AUTH_TOKEN', label: 'Auth Token', placeholder: '...' },
      { key: 'TWILIO_FROM_NUMBER', label: 'From Number', placeholder: '+1...' },
    ],
  },
]

function GoogleConnectionCard({ flashMsg }: { flashMsg: string }) {
  const [status, setStatus] = useState<{ connected: boolean; email: string } | null>(null)
  const [disconnecting, setDisconnecting] = useState(false)

  useEffect(() => {
    fetch('/auth/google/status')
      .then(r => r.json())
      .then(d => setStatus(d))
      .catch(() => setStatus({ connected: false, email: '' }))
  }, [flashMsg])

  const disconnect = async () => {
    setDisconnecting(true)
    await fetch('/auth/google/disconnect', { method: 'POST' })
    setStatus({ connected: false, email: '' })
    setDisconnecting(false)
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3.5">
        <div className="w-8 h-8 rounded-lg bg-[#1f2937] flex items-center justify-center shrink-0">
          <Cloud size={15} className="text-sky-400" />
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium text-gray-200">Google (Sheets, Drive, Docs, Calendar)</span>
          {status?.connected && (
            <p className="text-xs text-emerald-400 truncate">{status.email}</p>
          )}
        </div>
        {status?.connected
          ? <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
          : <XCircle size={13} className="text-gray-600 shrink-0" />
        }
      </div>

      {flashMsg && (
        <div className={`px-4 py-2 text-xs border-t border-[#1f2937] ${
          flashMsg.startsWith('Connected') ? 'text-emerald-400' : 'text-red-400'
        }`}>
          {flashMsg}
        </div>
      )}

      <div className="px-4 pb-4 pt-1 border-t border-[#1f2937]">
        <p className="text-xs text-gray-500 mt-2 mb-3">
          Sign in once to let all Google tools (Sheets, Drive, Docs, Calendar) use your account.
          Requires <code className="text-sky-400">GOOGLE_CLIENT_ID</code> and{' '}
          <code className="text-sky-400">GOOGLE_CLIENT_SECRET</code> in Replit Secrets.
        </p>
        {status?.connected ? (
          <Button variant="danger" size="sm" onClick={disconnect} disabled={disconnecting}>
            <LogOut size={13} />
            {disconnecting ? 'Disconnecting…' : 'Disconnect Google'}
          </Button>
        ) : (
          <a href="/auth/google">
            <Button variant="primary" size="sm">
              <LogIn size={13} />
              Connect with Google
            </Button>
          </a>
        )}
      </div>
    </div>
  )
}

function IntegrationCard({ integration }: { integration: Integration }) {
  const [expanded, setExpanded] = useState(false)
  const [values, setValues] = useState<Record<string, string>>(() => {
    try {
      return JSON.parse(localStorage.getItem(`creds_${integration.id}`) ?? '{}')
    } catch { return {} }
  })
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem(`creds_${integration.id}`, JSON.stringify(values))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const hasCredentials = Object.values(values).some(v => v)

  return (
    <div className="glass-card overflow-hidden">
      <button
        className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-[#1a2332] transition-colors text-left"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="w-8 h-8 rounded-lg bg-[#1f2937] flex items-center justify-center shrink-0">
          {integration.icon}
        </div>
        <span className="text-sm font-medium text-gray-200 flex-1">{integration.name}</span>
        {hasCredentials
          ? <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
          : <XCircle size={13} className="text-gray-600 shrink-0" />
        }
        {expanded ? <ChevronDown size={13} className="text-gray-500" /> : <ChevronRight size={13} className="text-gray-500" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-[#1f2937] space-y-3">
          <p className="text-xs text-gray-500 mt-2">
            Saved locally in your browser and sent to agents as needed.
          </p>
          {integration.fields.map(f => (
            f.textarea ? (
              <Textarea
                key={f.key}
                label={f.label}
                placeholder={f.placeholder}
                value={values[f.key] ?? ''}
                onChange={e => setValues(v => ({ ...v, [f.key]: e.target.value }))}
                rows={4}
              />
            ) : (
              <Input
                key={f.key}
                label={f.label}
                placeholder={f.placeholder}
                type={f.type}
                value={values[f.key] ?? ''}
                onChange={e => setValues(v => ({ ...v, [f.key]: e.target.value }))}
              />
            )
          ))}
          <div className="flex gap-2 pt-1">
            <Button variant="primary" size="sm" onClick={handleSave}>
              {saved ? <CheckCircle2 size={13} /> : <Key size={13} />}
              {saved ? 'Saved!' : 'Save'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [flashMsg, setFlashMsg] = useState('')

  useEffect(() => {
    const connected = searchParams.get('google_connected')
    const email = searchParams.get('email')
    const error = searchParams.get('google_error')
    if (connected) {
      setFlashMsg(`Connected as ${email || 'Google account'}`)
      setSearchParams({}, { replace: true })
    } else if (error) {
      setFlashMsg(`Error: ${decodeURIComponent(error)}`)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, setSearchParams])

  return (
    <div className="px-6 py-6 max-w-2xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon size={18} className="text-sky-400" />
        <h1 className="text-xl font-bold text-gray-100">Settings</h1>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-gray-500 mb-4">
          Configure your integrations. Credentials are stored in your browser and sent to agents when they run.
          For persistent server-side keys, use Replit Secrets.
        </p>
        <GoogleConnectionCard flashMsg={flashMsg} />
        {INTEGRATIONS.map(i => <IntegrationCard key={i.id} integration={i} />)}
      </div>
    </div>
  )
}
