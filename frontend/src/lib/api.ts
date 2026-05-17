const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || res.statusText)
  }
  return res.json()
}

// --- Agents ---
export interface Agent {
  id: number
  name: string
  description: string
  goal: string
  tools: string[]
  trigger: string
  status: string
  credentials: Record<string, string>
  sms_to?: string
  memory?: string
  webhook_token?: string
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  description?: string
  goal: string
  tools?: string[]
  trigger?: string
  credentials?: Record<string, string>
  sms_to?: string
}

export const agentsApi = {
  list: () => request<Agent[]>('/agents'),
  get: (id: number) => request<Agent>(`/agents/${id}`),
  create: (data: AgentCreate) => request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<AgentCreate>) =>
    request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) => request<void>(`/agents/${id}`, { method: 'DELETE' }),
  trigger: (id: number, input?: string) =>
    request<{ run_id: number }>(`/agents/${id}/trigger`, {
      method: 'POST',
      body: JSON.stringify({ input: input ?? '' }),
    }),
}

// --- Runs ---
export interface RunStep {
  tool: string
  input: Record<string, unknown>
  output: unknown
  error?: string
}

export interface Run {
  id: number
  agent_id: number
  trigger_type: string
  status: string
  plan?: string
  steps?: RunStep[]
  result?: string
  started_at: string
  completed_at?: string
}

export const runsApi = {
  list: (agentId?: number) =>
    request<Run[]>(agentId ? `/agents/${agentId}/runs` : '/runs'),
  get: (id: number) => request<Run>(`/runs/${id}`),
}

// --- Chat ---
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  agent_config?: AgentCreate
}

export const chatApi = {
  newAgent: (messages: ChatMessage[]) =>
    request<ChatResponse>('/chat/new', { method: 'POST', body: JSON.stringify({ messages }) }),
  withAgent: (id: number, messages: ChatMessage[]) =>
    request<ChatResponse>(`/agents/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),
}

// --- Sheets ---
export interface SheetPreview {
  headers: string[]
  rows: string[][]
  total_rows: number
}

export interface UploadResult {
  file_id: string
  filename: string
  rows: number
  columns: number
  preview: SheetPreview
}

export const sheetsApi = {
  uploadFile: async (file: File): Promise<UploadResult> => {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch(`${BASE}/sheets/upload`, { method: 'POST', body: fd })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  googlePreview: (url: string) =>
    request<SheetPreview>('/sheets/google/preview', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
  analyze: (data: { headers: string[]; rows: string[][] }) =>
    request<Record<string, unknown>>('/sheets/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}
