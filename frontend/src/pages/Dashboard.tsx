import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Bot, Play, CheckCircle2, TrendingUp, Plus, Zap } from 'lucide-react'
import { agentsApi, runsApi } from '../lib/api'
import AgentCard from '../components/agents/AgentCard'
import { Button } from '../components/ui/Button'

interface StatCardProps { label: string; value: string | number; icon: React.ReactNode; color: string }
function StatCard({ label, value, icon, color }: StatCardProps) {
  return (
    <div className="glass-card p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-100">{value}</p>
        <p className="text-xs text-gray-500 mt-0.5">{label}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: agents = [], isLoading } = useQuery({ queryKey: ['agents'], queryFn: agentsApi.list })
  const { data: runs = [] } = useQuery({ queryKey: ['runs'], queryFn: () => runsApi.list() })

  const today = new Date().toDateString()
  const runsToday = runs.filter(r => new Date(r.started_at).toDateString() === today)
  const successRate = runs.length
    ? Math.round((runs.filter(r => r.status === 'success').length / runs.length) * 100)
    : 0

  const lastRunByAgent = Object.fromEntries(
    agents.map(a => {
      const agentRuns = runs.filter(r => r.agent_id === a.id).sort(
        (x, y) => new Date(y.started_at).getTime() - new Date(x.started_at).getTime()
      )
      return [a.id, agentRuns[0]]
    })
  )

  return (
    <div className="px-6 py-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-100">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Your AI agents at a glance</p>
        </div>
        <Button variant="primary" onClick={() => navigate('/agents/new')}>
          <Plus size={14} /> New Agent
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Agents" value={agents.length} icon={<Bot size={18} className="text-sky-400" />} color="bg-sky-500/10" />
        <StatCard
          label="Active Agents"
          value={agents.filter(a => a.status === 'active').length}
          icon={<Zap size={18} className="text-emerald-400" />}
          color="bg-emerald-500/10"
        />
        <StatCard label="Runs Today" value={runsToday.length} icon={<Play size={18} className="text-violet-400" />} color="bg-violet-500/10" />
        <StatCard label="Success Rate" value={`${successRate}%`} icon={<TrendingUp size={18} className="text-orange-400" />} color="bg-orange-500/10" />
      </div>

      {/* Agents grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-300">Your Agents</h2>
          <span className="text-xs text-gray-500">{agents.length} total</span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="glass-card p-5 h-40 animate-pulse">
                <div className="flex gap-3 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-[#1f2937]" />
                  <div className="space-y-2 flex-1">
                    <div className="h-3 bg-[#1f2937] rounded w-1/2" />
                    <div className="h-2.5 bg-[#1f2937] rounded w-1/4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : agents.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <div className="w-14 h-14 rounded-2xl bg-sky-500/10 flex items-center justify-center mx-auto mb-4">
              <Bot size={28} className="text-sky-400" />
            </div>
            <p className="text-gray-400 text-sm mb-4">No agents yet. Create your first one.</p>
            <Button variant="primary" onClick={() => navigate('/agents/new')}>
              <Plus size={14} /> Create Agent
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {agents.map(agent => (
              <AgentCard key={agent.id} agent={agent} lastRun={lastRunByAgent[agent.id]} />
            ))}
            <button
              onClick={() => navigate('/agents/new')}
              className="glass-card p-5 flex flex-col items-center justify-center gap-2 text-gray-500 hover:text-gray-300 hover:border-[#374151] transition-all min-h-[160px] border-dashed"
            >
              <Plus size={20} />
              <span className="text-sm">New Agent</span>
            </button>
          </div>
        )}
      </div>

      {/* Recent runs */}
      {runs.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-300">Recent Runs</h2>
            <button onClick={() => navigate('/runs')} className="text-xs text-sky-400 hover:text-sky-300">View all</button>
          </div>
          <div className="glass-card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1f2937]">
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-400">Agent</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-400">Status</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-400">Trigger</th>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-gray-400">Started</th>
                </tr>
              </thead>
              <tbody>
                {runs.slice(0, 5).map(run => {
                  const agent = agents.find(a => a.id === run.agent_id)
                  return (
                    <tr key={run.id} className="border-b border-[#1f2937]/50 hover:bg-[#1a2332] transition-colors">
                      <td className="px-4 py-2.5 text-xs text-gray-300">{agent?.name ?? `Agent #${run.agent_id}`}</td>
                      <td className="px-4 py-2.5">
                        <span className={`tag ${run.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : run.status === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-sky-500/10 text-sky-400'}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{run.trigger_type}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{new Date(run.started_at).toLocaleString()}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
