import { useState, type ReactNode } from 'react'
import {
  Settings as SettingsIcon, Mail, MessageSquare, Github, Database, Cloud,
  CheckCircle2, XCircle, ChevronDown, ChevronRight, Key, ExternalLink,
} from 'lucide-react'
import { Input, Textarea } from '../components/ui/Input'
import { Button } from '../components/ui/Button'

interface Integration {
  id: string
  name: string
  icon: ReactNode
  fields: { key: string; label: string; placeholder: string; type?: string; textarea?: boolean }[]
  docsUrl?: string
}

const INTEGRATIONS: Integration[] = [
  {
    id: 'openai',
    name: 'AI Provider (OpenAI / Anthropic)',
    icon: <Key size={15} className="text-violet-400" />,
    fields: [
      { key: 'OPENAI_API_KEY', label: 'OpenAI API Key', placeholder: 'sk-...' },
      { key: 'ANTHROPIC_API_KEY', label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
      { key: 'AI_MODEL', label: 'Model', placeholder: 'gpt-4o-mini' },
    ],
  },
  {
    id: 'google',
    name: 'Google (Sheets, Drive, Calendar, Docs)',
    icon: <Cloud size={15} className="text-sky-400" />,
    fields: [
      { key: 'GOOGLE_SERVICE_ACCOUNT_JSON', label: 'Service Account JSON', placeholder: '{"type":"service_account",...}', textarea: true },
    ],
  },
  {
    id: 'gmail',
    name: 'Gmail',
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

function IntegrationCard({ integration }: { integration: Integration }) {
  const [expanded, setExpanded] = useState(false)
  const [values, setValues] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    localStorage.setItem(`creds_${integration.id}`, JSON.stringify(values))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const storedJson = localStorage.getItem(`creds_${integration.id}`)
  const hasCredentials = storedJson && Object.values(JSON.parse(storedJson) as Record<string, string>).some(v => v)

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
            These credentials are saved locally in your browser and sent to agents as needed.
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
  return (
    <div className="px-6 py-6 max-w-2xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon size={18} className="text-sky-400" />
        <h1 className="text-xl font-bold text-gray-100">Settings</h1>
      </div>

      <div className="space-y-2">
        <p className="text-xs text-gray-500 mb-4">
          Configure your integrations. Credentials are stored in your browser and sent to agents in their credential context.
          For production, set these as environment variables in your Replit secrets.
        </p>
        {INTEGRATIONS.map(i => <IntegrationCard key={i.id} integration={i} />)}
      </div>
    </div>
  )
}
