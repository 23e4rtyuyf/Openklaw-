import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Play, Trash2, ChevronRight, ChevronDown, Clock, Zap, Globe,
  CheckCircle2, XCircle, Loader2, Bot, MessageSquare,
} from 'lucide-react'
import { agentsApi, runsApi, type Run } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Dialog } from '../components/ui/Dialog'
import AgentBuilderChat from '../components/agents/AgentBuilderChat'
import { timeAgo, cn, readAllCredentials } from '../lib/utils'

function RunRow({ run }: { run: Run }) {
  const [expanded, setExpanded] = useState(false)

  const statusIcon = {
    success: <CheckCircle2 size={13} className="text-emerald-400" />,
    error: <XCircle size={13} className="text-red-400" />,
    failed: <XCircle size={13} className="text-red-400" />,
    running: <Loader2 size={13} className="text-sky-400 animate-spin" />,
  }[run.status] ?? <Clock size={13} className="text-gray-500" />

  return (
    <div className="border-b border-[#1f2937]/50">
      <button
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#1a2332] transition-colors text-left"
        onClick={() => setExpanded(e => !e)}
      >
        {statusIcon}
        <span className="text-xs text-gray-300 flex-1">{run.trigger_type}</span>
        <span className="text-[11px] text-gray-600">{timeAgo(run.started_at)}</span>
        {expanded ? <ChevronDown size={12} className="text-gray-500" /> : <ChevronRight size={12} className="text-gray-500" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {run.result && (
            <div className="bg-[#0d1117] rounded-lg p-3 text-xs text-gray-400 leading-relaxed">
              {run.result}
            </div>
          )}
          {run.steps && run.steps.length > 0 && (
            <div className="space-y-1">
              {run.steps.map((step, i) => (
                <div key={i} className="bg-[#0d1117] rounded-lg p-2.5 text-[11px]">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="font-medium text-sky-400">{step.tool}</span>
                    {step.error && <span className="text-red-400">— error</span>}
                  </div>
                  {step.error && <p className="text-red-400/80">{step.error}</p>}
                  {!step.error && step.output != null && (
                    <p className="text-gray-500 truncate">
                      {typeof step.output === 'string'
                        ? step.output.slice(0, 120)
                        : JSON.stringify(step.output).slice(0, 120)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>()
  const agentId = id ?? ''
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [chatOpen, setChatOpen] = useState(false)

  const { data: agent, isLoading } = useQuery({
    queryKey: ['agents', agentId],
    queryFn: () => agentsApi.get(agentId),
  })

  const { data: runs = [] } = useQuery({
    queryKey: ['runs', agentId],
    queryFn: () => runsApi.list(agentId),
    refetchInterval: 5000,
  })

  const trigger = useMutation({
    mutationFn: () => agentsApi.trigger(agentId, undefined, readAllCredentials()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['runs', agentId] }),
  })

  const del = useMutation({
    mutationFn: () => agentsApi.delete(agentId),
    onSuccess: () => navigate('/'),
  })

  if (isLoading || !agent) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 size={20} className="text-sky-400 animate-spin" />
      </div>
    )
  }

  return (
    <div className="px-5 py-5 max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} />
        </Button>
        <div className="flex items-center gap-3 flex-1">
          <div className="w-9 h-9 rounded-xl bg-sky-500/10 flex items-center justify-center">
            <Bot size={18} className="text-sky-400" />
          </div>
          <div>
            <h1 className="text-base font-bold text-gray-100">{agent.name}</h1>
            <Badge variant="status" status={agent.status}>{agent.status}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => setChatOpen(true)}>
            <MessageSquare size={13} /> Refine
          </Button>
          <Button variant="primary" size="sm" loading={trigger.isPending} onClick={() => trigger.mutate()}>
            <Play size={13} /> Run Now
          </Button>
          <Button variant="danger" size="sm" onClick={() => { if (confirm('Delete this agent?')) del.mutate() }}>
            <Trash2 size={13} />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Agent info */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card p-4 space-y-4">
            <section>
              <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Goal</p>
              <p className="text-sm text-gray-300 leading-relaxed">{agent.goal}</p>
            </section>

            {agent.description && (
              <section>
                <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Description</p>
                <p className="text-sm text-gray-400 leading-relaxed">{agent.description}</p>
              </section>
            )}

            <section>
              <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-1.5">Trigger</p>
              <div className="flex items-center gap-1.5 text-sm text-gray-300">
                {agent.trigger?.startsWith('cron') ? <Clock size={13} className="text-sky-400" /> : <Zap size={13} className="text-sky-400" />}
                <span className="font-mono text-xs">{agent.trigger || 'manual'}</span>
              </div>
            </section>

            {agent.tools?.length > 0 && (
              <section>
                <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider mb-2">Tools ({agent.tools.length})</p>
                <div className="flex flex-wrap gap-1.5">
                  {agent.tools.map(t => (
                    <span key={t} className="tag bg-[#1f2937] text-gray-400 text-[11px]">
                      {t.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>

          {/* Stats */}
          <div className="glass-card p-4 grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-lg font-bold text-gray-100">{runs.length}</p>
              <p className="text-[11px] text-gray-500">Total Runs</p>
            </div>
            <div>
              <p className="text-lg font-bold text-emerald-400">{runs.filter(r => r.status === 'success').length}</p>
              <p className="text-[11px] text-gray-500">Success</p>
            </div>
            <div>
              <p className="text-lg font-bold text-red-400">{runs.filter(r => r.status === 'error' || r.status === 'failed').length}</p>
              <p className="text-[11px] text-gray-500">Failed</p>
            </div>
          </div>
        </div>

        {/* Run history */}
        <div className="lg:col-span-3">
          <div className="glass-card overflow-hidden">
            <div className="px-4 py-3 border-b border-[#1f2937]">
              <h2 className="text-sm font-semibold text-gray-100">Run History</h2>
            </div>
            {runs.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No runs yet. Click "Run Now" to trigger manually.
              </div>
            ) : (
              runs.map(run => <RunRow key={run.id} run={run} />)
            )}
          </div>
        </div>
      </div>

      {/* Chat to refine dialog */}
      <Dialog open={chatOpen} onClose={() => setChatOpen(false)} title={`Refine "${agent.name}"`} size="lg">
        <div className="h-[60vh]">
          <AgentBuilderChat onCreated={() => { setChatOpen(false); queryClient.invalidateQueries({ queryKey: ['agents', agentId] }) }} />
        </div>
      </Dialog>
    </div>
  )
}
