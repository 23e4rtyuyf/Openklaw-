import { useNavigate } from 'react-router-dom'
import { Play, Bot, Clock, Zap, Globe, Calendar } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { agentsApi, type Agent } from '../../lib/api'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { timeAgo, statusBg } from '../../lib/utils'

const TRIGGER_ICONS: Record<string, React.ReactNode> = {
  cron: <Clock size={11} />,
  webhook: <Globe size={11} />,
  manual: <Zap size={11} />,
  schedule: <Calendar size={11} />,
}

interface AgentCardProps {
  agent: Agent
  lastRun?: { status: string; completed_at?: string; result?: string }
}

export default function AgentCard({ agent, lastRun }: AgentCardProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const trigger = useMutation({
    mutationFn: () => agentsApi.trigger(agent.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })

  const triggerType = agent.trigger?.split(' ')[0] ?? 'manual'

  return (
    <div
      className="glass-card-hover p-5 cursor-pointer group"
      onClick={() => navigate(`/agents/${agent.id}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center">
            <Bot size={16} className="text-sky-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-100 leading-tight">{agent.name}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`tag ${statusBg(agent.status)}`}>
                <span className={`w-1.5 h-1.5 rounded-full inline-block ${agent.status === 'active' ? 'bg-emerald-400' : 'bg-gray-500'}`} />
                {agent.status}
              </span>
            </div>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          loading={trigger.isPending}
          onClick={e => { e.stopPropagation(); trigger.mutate() }}
          className="opacity-0 group-hover:opacity-100 text-sky-400"
        >
          <Play size={13} />
        </Button>
      </div>

      {/* Description */}
      {agent.description && (
        <p className="text-xs text-gray-500 leading-relaxed mb-3 line-clamp-2">{agent.description}</p>
      )}

      {/* Tools */}
      {agent.tools?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {agent.tools.slice(0, 4).map(t => (
            <span key={t} className="tag bg-[#1f2937] text-gray-400 text-[10px]">{t.replace(/_/g, ' ')}</span>
          ))}
          {agent.tools.length > 4 && (
            <span className="tag bg-[#1f2937] text-gray-500 text-[10px]">+{agent.tools.length - 4}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-[#1f2937]">
        <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
          {TRIGGER_ICONS[triggerType] ?? <Zap size={11} />}
          <span>{agent.trigger || 'manual'}</span>
        </div>
        {lastRun && (
          <div className="flex items-center gap-1.5">
            <Badge variant="status" status={lastRun.status} className="text-[10px]">
              {lastRun.status}
            </Badge>
            <span className="text-[11px] text-gray-600">
              {lastRun.completed_at ? timeAgo(lastRun.completed_at) : '—'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
