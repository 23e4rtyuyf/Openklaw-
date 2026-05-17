import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import AgentBuilderChat from '../components/agents/AgentBuilderChat'
import { Button } from '../components/ui/Button'

export default function AgentCreate() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-screen animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-3.5 border-b border-[#1f2937]">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} />
        </Button>
        <div>
          <h1 className="text-sm font-semibold text-gray-100">Create Agent</h1>
          <p className="text-xs text-gray-500">Describe your automation in plain English</p>
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 min-h-0">
        <AgentBuilderChat onCreated={id => navigate(`/agents/${id}`)} />
      </div>
    </div>
  )
}
