import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi, agentsApi, type ChatMessage, type AgentCreate } from '../../lib/api'
import { Button } from '../ui/Button'
import { cn, readAllCredentials } from '../../lib/utils'

interface Props {
  onCreated?: (id: string) => void
}

const SUGGESTIONS = [
  'Monitor my Gmail for invoices and log them to a Google Sheet',
  'Post daily weather updates to Slack at 8am',
  'Summarize new GitHub issues and email me a digest',
  'Alert me on Slack when a CSV file changes in Drive',
]

export default function AgentBuilderChat({ onCreated }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [pendingConfig, setPendingConfig] = useState<AgentCreate | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const chat = useMutation({
    mutationFn: (msgs: ChatMessage[]) => chatApi.newAgent(msgs),
    onSuccess: (data) => {
      setMessages(m => [...m, { role: 'assistant', content: data.reply }])
      if (data.agent_config) {
        // Remap suggested_trigger → trigger and attach stored credentials
        const raw = data.agent_config as unknown as Record<string, unknown>
        const config: AgentCreate = {
          ...(raw as unknown as AgentCreate),
          trigger: (raw.suggested_trigger ?? raw.trigger) as AgentCreate['trigger'],
          credentials: readAllCredentials(),
        }
        setPendingConfig(config)
      }
    },
  })

  const deploy = useMutation({
    mutationFn: (config: AgentCreate) =>
      agentsApi.create({ ...config, credentials: { ...readAllCredentials(), ...(config.credentials ?? {}) } }),
    onSuccess: (agent) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] })
      onCreated?.(agent.id)
    },
  })

  const send = () => {
    if (!input.trim() || chat.isPending) return
    const next: ChatMessage[] = [...messages, { role: 'user', content: input.trim() }]
    setMessages(next)
    setInput('')
    chat.mutate(next)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/10 flex items-center justify-center mx-auto mb-4">
              <Bot size={28} className="text-sky-400" />
            </div>
            <p className="text-gray-400 text-sm mb-6">Describe your agent in plain English</p>
            <div className="grid grid-cols-1 gap-2 max-w-md mx-auto">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="text-left px-3.5 py-2.5 rounded-lg bg-[#111827] border border-[#1f2937] hover:border-[#374151] text-xs text-gray-400 hover:text-gray-200 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={cn('flex gap-3', m.role === 'user' && 'justify-end')}>
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-sky-500/10 flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={14} className="text-sky-400" />
              </div>
            )}
            <div
              className={cn(
                'max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed',
                m.role === 'user'
                  ? 'bg-sky-500 text-white rounded-tr-sm'
                  : 'bg-[#111827] border border-[#1f2937] text-gray-200 rounded-tl-sm'
              )}
            >
              {m.content}
            </div>
            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-[#1f2937] flex items-center justify-center shrink-0 mt-0.5">
                <User size={14} className="text-gray-400" />
              </div>
            )}
          </div>
        ))}

        {chat.isPending && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-sky-500/10 flex items-center justify-center shrink-0">
              <Loader2 size={14} className="text-sky-400 animate-spin" />
            </div>
            <div className="bg-[#111827] border border-[#1f2937] rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <span key={i} className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        {pendingConfig && !chat.isPending && (
          <div className="bg-[#0d1117] border border-sky-500/30 rounded-xl p-4">
            <p className="text-xs font-medium text-sky-400 mb-2">Agent ready to deploy</p>
            <p className="text-sm font-semibold text-gray-100 mb-1">{pendingConfig.name}</p>
            <p className="text-xs text-gray-500 mb-3">{pendingConfig.goal?.slice(0, 120)}</p>
            <div className="flex flex-wrap gap-1 mb-3">
              {(pendingConfig.tools ?? []).map(t => (
                <span key={t} className="tag bg-sky-500/10 text-sky-400 text-[10px]">{t}</span>
              ))}
            </div>
            <Button
              variant="primary"
              size="sm"
              loading={deploy.isPending}
              onClick={() => deploy.mutate(pendingConfig)}
            >
              Deploy Agent
            </Button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#1f2937] px-4 py-3">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-[#111827] border border-[#1f2937] rounded-xl px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-sky-500/60 transition-colors"
            placeholder="Describe what your agent should do..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          />
          <Button variant="primary" size="md" onClick={send} disabled={!input.trim() || chat.isPending}>
            <Send size={14} />
          </Button>
        </div>
      </div>
    </div>
  )
}
