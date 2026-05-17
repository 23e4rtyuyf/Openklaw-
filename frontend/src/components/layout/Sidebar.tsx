import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Table2, Bot, History, Settings, Plus, Zap, ChevronLeft, ChevronRight,
} from 'lucide-react'
import { cn } from '../../lib/utils'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/sheets', icon: Table2, label: 'Spreadsheets' },
  { to: '/runs', icon: History, label: 'Run History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()

  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-[#0d1117] border-r border-[#1f2937] transition-all duration-200 shrink-0',
        collapsed ? 'w-14' : 'w-56'
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-3.5 h-14 border-b border-[#1f2937]">
        <div className="w-7 h-7 rounded-lg bg-sky-500 flex items-center justify-center shrink-0">
          <Zap size={14} className="text-white" />
        </div>
        {!collapsed && (
          <span className="font-semibold text-sm text-gray-100 truncate">OpenKlaw</span>
        )}
      </div>

      {/* New Agent button */}
      <div className="px-2 py-3">
        <button
          onClick={() => navigate('/agents/new')}
          className={cn(
            'w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-sm font-medium transition-colors',
            collapsed && 'justify-center'
          )}
        >
          <Plus size={14} />
          {!collapsed && 'New Agent'}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              cn('sidebar-item', isActive && 'active', collapsed && 'justify-center')
            }
          >
            <Icon size={16} className="shrink-0" />
            {!collapsed && <span className="truncate">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(c => !c)}
        className="flex items-center justify-center h-10 border-t border-[#1f2937] text-gray-500 hover:text-gray-300 transition-colors"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </aside>
  )
}
