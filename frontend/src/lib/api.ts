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
  id: string
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
  trigger?: Record<string, unknown>
  credentials?: Record<string, string>
  sms_to?: string
}

export const agentsApi = {
  list: () => request<Agent[]>('/agents'),
  get: (id: string) => request<Agent>(`/agents/${id}`),
  create: (data: AgentCreate) => request<Agent>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<AgentCreate>) =>
    request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/agents/${id}`, { method: 'DELETE' }),
  trigger: (id: string, input?: string, credentials?: Record<string, string>) =>
    request<{ run_id: string }>(`/agents/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ input: input ?? '', credentials }),
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
  id: string
  agent_id: string
  trigger_type: string
  status: string
  plan?: string
  steps?: RunStep[]
  result?: string
  started_at: string
  completed_at?: string
}

export const runsApi = {
  list: (agentId?: string) =>
    request<Run[]>(agentId ? `/runs?agent_id=${agentId}` : '/runs'),
  get: (id: string) => request<Run>(`/runs/${id}`),
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
    request<ChatResponse>('/agents/chat/new', {
      method: 'POST',
      body: JSON.stringify({ message: messages.at(-1)?.content ?? '' }),
    }),
  withAgent: (id: string, messages: ChatMessage[]) =>
    request<ChatResponse>(`/agents/${id}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message: messages.at(-1)?.content ?? '' }),
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
