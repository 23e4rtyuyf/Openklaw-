import { useQuery } from '@tanstack/react-query'
import { runsApi, agentsApi } from '../lib/api'
import { CheckCircle2, XCircle, Loader2, Clock, History } from 'lucide-react'
import { timeAgo } from '../lib/utils'
import { useNavigate } from 'react-router-dom'

export default function RunHistory() {
  const navigate = useNavigate()
  const { data: runs = [], isLoading } = useQuery({ queryKey: ['runs'], queryFn: () => runsApi.list() })
  const { data: agents = [] } = useQuery({ queryKey: ['agents'], queryFn: agentsApi.list })

  const agentMap = Object.fromEntries(agents.map(a => [a.id, a]))

  const statusIcon = (s: string) => ({
    success: <CheckCircle2 size={13} className="text-emerald-400" />,
    error: <XCircle size={13} className="text-red-400" />,
    failed: <XCircle size={13} className="text-red-400" />,
    running: <Loader2 size={13} className="text-sky-400 animate-spin" />,
  }[s] ?? <Clock size={13} className="text-gray-500" />)

  return (
    <div className="px-6 py-6 max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <History size={18} className="text-sky-400" />
        <h1 className="text-xl font-bold text-gray-100">Run History</h1>
        <span className="text-xs text-gray-500 ml-auto">{runs.length} total</span>
      </div>

      {isLoading ? (
        <div className="glass-card p-12 flex items-center justify-center">
          <Loader2 size={20} className="text-sky-400 animate-spin" />
        </div>
      ) : runs.length === 0 ? (
        <div className="glass-card p-12 text-center text-sm text-gray-500">No runs yet</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#1f2937]">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Status</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Agent</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Trigger</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Result</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Started</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400">Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => {
                const agent = agentMap[run.agent_id]
                const duration = run.completed_at
                  ? ((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000).toFixed(1) + 's'
                  : '—'
                return (
                  <tr
                    key={run.id}
                    className="border-b border-[#1f2937]/50 hover:bg-[#1a2332] transition-colors cursor-pointer"
                    onClick={() => agent && navigate(`/agents/${agent.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {statusIcon(run.status)}
                        <span className="text-xs text-gray-400">{run.status}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-300">
                      {agent?.name ?? `Agent #${run.agent_id}`}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{run.trigger_type}</td>
                    <td className="px-4 py-3 text-xs text-gray-500 max-w-[200px] truncate">
                      {run.result ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                      {timeAgo(run.started_at)}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-500">{duration}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
