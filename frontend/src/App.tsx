import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Sheets from './pages/Sheets'
import AgentCreate from './pages/AgentCreate'
import AgentDetail from './pages/AgentDetail'
import RunHistory from './pages/RunHistory'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="sheets" element={<Sheets />} />
        <Route path="agents/new" element={<AgentCreate />} />
        <Route path="agents/:id" element={<AgentDetail />} />
        <Route path="runs" element={<RunHistory />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
