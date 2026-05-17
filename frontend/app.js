const { useState, useEffect, useRef, useCallback } = React;

// ── API helpers ──────────────────────────────────────────────────────────────
const api = {
  get: (path) => fetch(path).then(r => r.json()),
  post: (path, body) => fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
  put: (path, body) => fetch(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
  del: (path) => fetch(path, { method: 'DELETE' }).then(r => r.json()),
};

// ── Utilities ────────────────────────────────────────────────────────────────
function timeAgo(dt) {
  if (!dt) return '—';
  const d = new Date(dt + 'Z');
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s/60)}m ago`;
  if (s < 86400) return `${Math.floor(s/3600)}h ago`;
  return d.toLocaleDateString();
}

function StatusBadge({ status }) {
  const map = {
    active: ['badge-active', '🟢 Active'],
    paused: ['badge-paused', '⏸ Paused'],
    draft:  ['badge-draft',  '📝 Draft'],
    success: ['badge-success', '✓ Success'],
    failed:  ['badge-failed', '✗ Failed'],
    running: ['badge-running', '⟳ Running'],
  };
  const [cls, label] = map[status] || ['badge-draft', status];
  return <span className={`badge ${cls}`}>{label}</span>;
}

function TriggerChip({ trigger }) {
  const t = trigger?.type || 'manual';
  const icons = { manual: '▶', cron: '⏰', webhook: '🔗' };
  const labels = { manual: 'Manual', cron: trigger?.config?.cron || 'Cron', webhook: 'Webhook' };
  return (
    <span className="badge" style={{ background: '#0f172a', color: '#94a3b8', border: '1px solid #1e293b' }}>
      {icons[t]} {labels[t]}
    </span>
  );
}

function Spinner() {
  return <div className="spinner" />;
}

// ── Layout ───────────────────────────────────────────────────────────────────
function Layout({ page, setPage, children }) {
  const links = [
    { id: 'dashboard', icon: '⚡', label: 'Agents' },
    { id: 'runs', icon: '📋', label: 'Run History' },
    { id: 'settings', icon: '⚙️', label: 'Settings' },
  ];
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside style={{ width: 220, background: '#0d1117', borderRight: '1px solid #1f2937', padding: '24px 12px', flexShrink: 0 }}>
        <div style={{ padding: '0 8px 24px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 22 }}>⚡</span>
          <span style={{ fontWeight: 700, fontSize: 18, color: '#f9fafb' }}>OpenKlaw</span>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {links.map(l => (
            <a key={l.id} className={`sidebar-link ${page === l.id ? 'active' : ''}`}
               onClick={() => setPage(l.id)}>
              <span>{l.icon}</span>
              <span>{l.label}</span>
            </a>
          ))}
        </nav>
        <div style={{ marginTop: 'auto', paddingTop: 24, fontSize: 11, color: '#4b5563', padding: '24px 8px 0' }}>
          Open-source AI Superagents
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: 'auto', maxHeight: '100vh' }}>
        {children}
      </main>
    </div>
  );
}

// ── Dashboard ────────────────────────────────────────────────────────────────
function Dashboard({ setPage, setSelectedAgent }) {
  const [agents, setAgents] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    const [a, r] = await Promise.all([api.get('/api/agents'), api.get('/api/runs?limit=20')]);
    setAgents(a);
    setRuns(r);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, []);

  async function toggleStatus(agent) {
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    await api.put(`/api/agents/${agent.id}`, { status: newStatus });
    load();
  }

  async function deleteAgent(id) {
    if (!confirm('Delete this agent?')) return;
    await api.del(`/api/agents/${id}`);
    load();
  }

  async function runNow(agent) {
    await api.post(`/api/agents/${agent.id}/run`, { input_data: {} });
    setTimeout(load, 1000);
  }

  function lastRun(agentId) {
    return runs.find(r => r.agent_id === agentId);
  }

  const activeCount = agents.filter(a => a.status === 'active').length;
  const todayRuns = runs.filter(r => {
    const d = new Date(r.started_at + 'Z');
    const n = new Date();
    return d.toDateString() === n.toDateString();
  });
  const successRate = todayRuns.length
    ? Math.round(todayRuns.filter(r => r.status === 'success').length / todayRuns.length * 100)
    : 0;

  return (
    <div style={{ padding: 32 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f9fafb', margin: 0 }}>Your Superagents</h1>
          <p style={{ color: '#6b7280', marginTop: 4, fontSize: 14 }}>Autonomous AI agents running 24/7</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setCreating(true); }}>
          ＋ New Agent
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Total Agents', value: agents.length, icon: '🤖' },
          { label: 'Active', value: activeCount, icon: '🟢' },
          { label: "Today's Success Rate", value: `${successRate}%`, icon: '✓' },
        ].map(stat => (
          <div key={stat.label} className="card" style={{ padding: 20 }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>{stat.icon}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#f9fafb' }}>{stat.value}</div>
            <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 60 }}><Spinner /></div>}

      {/* Empty state */}
      {!loading && agents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>⚡</div>
          <h2 style={{ color: '#f9fafb', marginBottom: 8 }}>Create your first Superagent</h2>
          <p style={{ color: '#6b7280', marginBottom: 24 }}>Describe what you want it to do in plain English</p>
          <button className="btn btn-primary" onClick={() => setCreating(true)}>+ New Agent</button>
        </div>
      )}

      {/* Agent cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
        {agents.map(agent => {
          const run = lastRun(agent.id);
          return (
            <div key={agent.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{ fontWeight: 600, fontSize: 16, color: '#f9fafb', margin: 0, marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {agent.name}
                  </h3>
                  <StatusBadge status={agent.status} />
                </div>
                <TriggerChip trigger={agent.trigger} />
              </div>

              <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16, lineHeight: 1.5 }}>
                {agent.goal || agent.description}
              </p>

              {run && (
                <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 16, padding: '8px 12px', background: '#0f172a', borderRadius: 6 }}>
                  <span style={{ marginRight: 8 }}>Last run: {timeAgo(run.started_at)}</span>
                  <StatusBadge status={run.status} />
                  {run.result && <div style={{ marginTop: 4, color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.result}</div>}
                </div>
              )}

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button className="btn btn-primary btn-sm" onClick={() => runNow(agent)}>▶ Run</button>
                <button className="btn btn-secondary btn-sm" onClick={() => { setSelectedAgent(agent); setPage('agent-chat'); }}>💬 Chat</button>
                <button className="btn btn-secondary btn-sm" onClick={() => { setSelectedAgent(agent); setPage('agent-detail'); }}>📋 Logs</button>
                <button className="btn btn-secondary btn-sm" onClick={() => toggleStatus(agent)}>
                  {agent.status === 'active' ? '⏸' : '▶'} {agent.status === 'active' ? 'Pause' : 'Activate'}
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => deleteAgent(agent.id)}>🗑</button>
              </div>
            </div>
          );
        })}
      </div>

      {creating && <NewAgentModal onClose={() => setCreating(false)} onCreated={(a) => { setCreating(false); setSelectedAgent(a); setPage('agent-chat'); }} />}
    </div>
  );
}

// ── New Agent Modal (chat-based creation) ─────────────────────────────────────
function NewAgentModal({ onClose, onCreated }) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [agentConfig, setAgentConfig] = useState(null);
  const [agentId, setAgentId] = useState(null);
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  async function send() {
    if (!message.trim() || loading) return;
    const text = message.trim();
    setMessage('');
    setMessages(m => [...m, { role: 'user', content: text }]);
    setLoading(true);

    try {
      let resp;
      if (!agentId) {
        resp = await api.post('/api/agents/chat/new', { message: text });
        if (resp.agent_config) {
          const agents = await api.get('/api/agents');
          const newest = agents[0];
          if (newest) setAgentId(newest.id);
        }
      } else {
        resp = await api.post(`/api/agents/${agentId}/chat`, { message: text });
      }
      setMessages(m => [...m, { role: 'assistant', content: resp.reply }]);
      if (resp.agent_config) setAgentConfig(resp.agent_config);
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', content: 'Error: ' + e.message }]);
    }
    setLoading(false);
  }

  async function deploy() {
    if (!agentId) return;
    await api.put(`/api/agents/${agentId}`, { status: 'active' });
    const agent = await api.get(`/api/agents/${agentId}`);
    onCreated(agent);
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 16, width: '90%', maxWidth: 680, height: '80vh', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>⚡ Create a Superagent</h2>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#6b7280' }}>Describe what you want your agent to do</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#6b7280', fontSize: 20, cursor: 'pointer' }}>✕</button>
        </div>

        {/* Chat */}
        <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#6b7280', marginTop: 40 }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>💬</div>
              <p>Tell me what you want to automate. For example:</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16, alignItems: 'center' }}>
                {[
                  "Monitor Hacker News daily for AI agent posts and summarize them",
                  "Check our competitor's pricing page every morning and alert me to changes",
                  "Fetch crypto prices every hour and send a report to Telegram"
                ].map(ex => (
                  <button key={ex} onClick={() => setMessage(ex)}
                    style={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8, padding: '8px 16px', color: '#9ca3af', cursor: 'pointer', fontSize: 13, maxWidth: 400, textAlign: 'left' }}>
                    "{ex}"
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div className={m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>{m.content}</div>
            </div>
          ))}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div className="chat-bubble-ai" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Spinner /> Thinking...
              </div>
            </div>
          )}
        </div>

        {/* Input + actions */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid #1f2937' }}>
          {agentConfig && (
            <div style={{ background: '#0f172a', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 13, color: '#94a3b8' }}>
              <span style={{ color: '#4ade80', marginRight: 8 }}>✓</span>
              Agent "{agentConfig.name}" configured — {agentConfig.tools?.length || 0} tools, {agentConfig.suggested_trigger?.type || 'manual'} trigger
              {agentId && (
                <button className="btn btn-primary btn-sm" style={{ marginLeft: 12 }} onClick={deploy}>
                  🚀 Deploy Agent
                </button>
              )}
            </div>
          )}
          <div style={{ display: 'flex', gap: 10 }}>
            <input
              className="input"
              placeholder="Describe your agent or refine it..."
              value={message}
              onChange={e => setMessage(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={send} disabled={loading || !message.trim()}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Agent Chat (refine existing agent) ───────────────────────────────────────
function AgentChat({ agent, setPage, setSelectedAgent }) {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(agent);
  const chatRef = useRef(null);

  useEffect(() => {
    api.get(`/api/agents/${agent.id}/messages`).then(setMessages);
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  async function send() {
    if (!message.trim() || loading) return;
    const text = message.trim();
    setMessage('');
    setMessages(m => [...m, { id: Date.now(), role: 'user', content: text }]);
    setLoading(true);
    try {
      const resp = await api.post(`/api/agents/${agent.id}/chat`, { message: text });
      setMessages(resp.messages);
      if (resp.agent_config) {
        const updated = await api.get(`/api/agents/${agent.id}`);
        setCurrentAgent(updated);
        setSelectedAgent(updated);
      }
    } catch (e) {
      setMessages(m => [...m, { id: Date.now(), role: 'assistant', content: 'Error: ' + e.message }]);
    }
    setLoading(false);
  }

  async function runNow() {
    await api.post(`/api/agents/${agent.id}/run`, { input_data: {} });
    setPage('agent-detail');
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <div style={{ padding: '20px 32px', borderBottom: '1px solid #1f2937', display: 'flex', gap: 16, alignItems: 'center' }}>
        <button className="btn btn-secondary btn-sm" onClick={() => setPage('dashboard')}>← Back</button>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>{currentAgent.name}</h2>
          <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
            <StatusBadge status={currentAgent.status} />
            <TriggerChip trigger={currentAgent.trigger} />
          </div>
        </div>
        <button className="btn btn-primary btn-sm" onClick={runNow}>▶ Run Now</button>
        <button className="btn btn-secondary btn-sm" onClick={() => setPage('agent-detail')}>📋 Logs</button>
      </div>

      {/* Chat */}
      <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#6b7280', marginTop: 40 }}>
            <p>Chat with your agent to refine it. Try:</p>
            <p style={{ color: '#94a3b8' }}>"Make it run twice a day" · "Also save results to memory" · "Add Telegram notifications"</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={m.id || i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div className={m.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}>{m.content}</div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex' }}>
            <div className="chat-bubble-ai" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Spinner /> Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '16px 32px', borderTop: '1px solid #1f2937', display: 'flex', gap: 10 }}>
        <input
          className="input"
          placeholder="Refine your agent..."
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          disabled={loading}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading || !message.trim()}>Send</button>
      </div>
    </div>
  );
}

// ── Agent Detail (runs + settings) ───────────────────────────────────────────
function AgentDetail({ agent, setPage }) {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agentData, setAgentData] = useState(agent);

  useEffect(() => {
    Promise.all([
      api.get(`/api/runs?agent_id=${agent.id}`),
      api.get(`/api/agents/${agent.id}`),
    ]).then(([r, a]) => { setRuns(r); setAgentData(a); setLoading(false); });
  }, []);

  async function runNow() {
    await api.post(`/api/agents/${agent.id}/run`, { input_data: {} });
    setTimeout(() => api.get(`/api/runs?agent_id=${agent.id}`).then(setRuns), 2000);
  }

  return (
    <div style={{ padding: 32 }}>
      <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 24 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => setPage('dashboard')}>← Back</button>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, flex: 1 }}>{agentData.name}</h2>
        <button className="btn btn-secondary btn-sm" onClick={() => setPage('agent-chat')}>💬 Chat</button>
        <button className="btn btn-primary" onClick={runNow}>▶ Run Now</button>
      </div>

      {/* Agent info */}
      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
          <StatusBadge status={agentData.status} />
          <TriggerChip trigger={agentData.trigger} />
          {agentData.tools?.map(t => (
            <span key={t} className="badge" style={{ background: '#0f172a', color: '#64748b', border: '1px solid #1e293b', fontSize: 11 }}>{t}</span>
          ))}
        </div>
        <p style={{ color: '#9ca3af', fontSize: 14 }}>{agentData.goal || agentData.description}</p>
        {agentData.webhook_token && (
          <div style={{ marginTop: 12, fontSize: 12, color: '#6b7280' }}>
            Webhook URL: <code style={{ color: '#94a3b8' }}>{window.location.origin}/trigger/{agentData.webhook_token}</code>
          </div>
        )}
      </div>

      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Run History</h3>
      {loading && <Spinner />}
      <div style={{ display: 'flex', gap: 16 }}>
        {/* Run list */}
        <div style={{ flex: 1 }}>
          {runs.map(run => (
            <div key={run.id} onClick={() => setSelectedRun(run)}
              className="card" style={{ padding: 16, marginBottom: 8, cursor: 'pointer', borderColor: selectedRun?.id === run.id ? '#0ea5e9' : undefined }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <StatusBadge status={run.status} />
                  <span style={{ fontSize: 12, color: '#6b7280' }}>{run.trigger_type}</span>
                </div>
                <span style={{ fontSize: 12, color: '#6b7280' }}>{timeAgo(run.started_at)}</span>
              </div>
              {run.result && <p style={{ margin: '8px 0 0', fontSize: 13, color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.result}</p>}
            </div>
          ))}
          {!loading && runs.length === 0 && <p style={{ color: '#6b7280' }}>No runs yet. Click "Run Now" to start.</p>}
        </div>

        {/* Run detail panel */}
        {selectedRun && (
          <div className="card" style={{ width: 400, padding: 20, flexShrink: 0, maxHeight: '70vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <StatusBadge status={selectedRun.status} />
              <button onClick={() => setSelectedRun(null)} style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer' }}>✕</button>
            </div>
            {selectedRun.result && (
              <div style={{ marginBottom: 16, padding: 12, background: '#0f172a', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>RESULT</div>
                <p style={{ fontSize: 14, color: '#e2e8f0', margin: 0 }}>{selectedRun.result}</p>
              </div>
            )}
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>STEPS ({selectedRun.steps?.length || 0})</div>
            {(selectedRun.steps || []).map((step, i) => (
              <div key={i} className={`step-item ${step.ok ? 'ok' : 'fail'}`} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: step.ok ? '#4ade80' : '#f87171' }}>
                    {step.ok ? '✓' : '✗'} {step.tool}
                  </span>
                </div>
                {step.input && (
                  <details style={{ fontSize: 11, color: '#6b7280' }}>
                    <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Input</summary>
                    <pre style={{ marginTop: 4, fontSize: 11 }}><code>{JSON.stringify(step.input, null, 2)}</code></pre>
                  </details>
                )}
                {step.output !== null && step.output !== undefined && (
                  <details style={{ fontSize: 11, marginTop: 4 }}>
                    <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Output</summary>
                    <pre style={{ marginTop: 4, fontSize: 11 }}><code>
                      {typeof step.output === 'string' ? step.output.slice(0, 500) : JSON.stringify(step.output, null, 2)}
                    </code></pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Run History ───────────────────────────────────────────────────────────────
function RunHistory() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.get('/api/runs?limit=100').then(r => { setRuns(r); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: 32 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Run History</h1>
      {loading && <Spinner />}
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          {runs.map(run => (
            <div key={run.id} onClick={() => setSelected(run)}
              className="card" style={{ padding: 16, marginBottom: 8, cursor: 'pointer', borderColor: selected?.id === run.id ? '#0ea5e9' : undefined }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <StatusBadge status={run.status} />
                  <span style={{ fontSize: 12, color: '#6b7280', background: '#0f172a', padding: '2px 8px', borderRadius: 4 }}>{run.trigger_type}</span>
                  <span style={{ fontSize: 12, color: '#6b7280' }}>Agent: {run.agent_id.slice(0, 8)}...</span>
                </div>
                <span style={{ fontSize: 12, color: '#6b7280' }}>{timeAgo(run.started_at)}</span>
              </div>
              {run.result && <p style={{ margin: 0, fontSize: 13, color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{run.result}</p>}
            </div>
          ))}
          {!loading && runs.length === 0 && <p style={{ color: '#6b7280' }}>No runs yet.</p>}
        </div>

        {selected && (
          <div className="card" style={{ width: 400, padding: 20, flexShrink: 0, maxHeight: '80vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <StatusBadge status={selected.status} />
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer' }}>✕</button>
            </div>
            {selected.result && (
              <div style={{ marginBottom: 16, padding: 12, background: '#0f172a', borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>RESULT</div>
                <p style={{ fontSize: 14, color: '#e2e8f0', margin: 0 }}>{selected.result}</p>
              </div>
            )}
            {(selected.steps || []).map((step, i) => (
              <div key={i} className={`step-item ${step.ok ? 'ok' : 'fail'}`} style={{ marginBottom: 12 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: step.ok ? '#4ade80' : '#f87171' }}>
                  {step.ok ? '✓' : '✗'} {step.tool}
                </span>
                <details style={{ fontSize: 11, marginTop: 4 }}>
                  <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Details</summary>
                  <pre style={{ marginTop: 4 }}><code>{JSON.stringify({ input: step.input, output: step.output }, null, 2)}</code></pre>
                </details>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Settings ──────────────────────────────────────────────────────────────────
function Settings() {
  return (
    <div style={{ padding: 32, maxWidth: 600 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Settings</h1>
      <p style={{ color: '#6b7280', marginBottom: 32 }}>Configure OpenKlaw via environment variables in your <code>.env</code> file.</p>

      {[
        { key: 'AI_PROVIDER', desc: 'openai | anthropic | openai_compatible', example: 'openai' },
        { key: 'AI_MODEL', desc: 'Model to use', example: 'gpt-4o-mini' },
        { key: 'AI_BASE_URL', desc: 'For OpenAI-compatible endpoints (Ollama, OpenRouter)', example: 'http://localhost:11434/v1' },
        { key: 'OPENAI_API_KEY', desc: 'OpenAI API key', example: 'sk-...' },
        { key: 'ANTHROPIC_API_KEY', desc: 'Anthropic API key', example: 'sk-ant-...' },
        { key: 'TELEGRAM_BOT_TOKEN', desc: 'Telegram bot token (optional)', example: '123456:ABC...' },
      ].map(v => (
        <div key={v.key} className="card" style={{ padding: 16, marginBottom: 12 }}>
          <code style={{ color: '#60a5fa', fontSize: 14 }}>{v.key}</code>
          <p style={{ margin: '4px 0', fontSize: 13, color: '#9ca3af' }}>{v.desc}</p>
          <p style={{ margin: 0, fontSize: 12, color: '#6b7280' }}>Example: <code style={{ color: '#94a3b8' }}>{v.example}</code></p>
        </div>
      ))}

      <div className="card" style={{ padding: 20, marginTop: 24 }}>
        <h3 style={{ margin: '0 0 12px', fontSize: 15 }}>Telegram Setup</h3>
        <ol style={{ color: '#9ca3af', fontSize: 13, paddingLeft: 20, lineHeight: 2 }}>
          <li>Create a bot with <a href="https://t.me/BotFather" style={{ color: '#0ea5e9' }}>@BotFather</a> on Telegram</li>
          <li>Copy the bot token to <code>TELEGRAM_BOT_TOKEN</code> in your .env</li>
          <li>Message your bot to get your chat ID (or use @userinfobot)</li>
          <li>Set the chat ID in each agent's settings</li>
          <li>Point Telegram webhook to: <code>{window.location.origin}/telegram</code></li>
        </ol>
      </div>
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────
function App() {
  const [page, setPage] = useState('dashboard');
  const [selectedAgent, setSelectedAgent] = useState(null);

  const navigate = (p, agent = null) => {
    if (agent) setSelectedAgent(agent);
    setPage(p);
  };

  let content;
  if (page === 'dashboard') {
    content = <Dashboard setPage={navigate} setSelectedAgent={setSelectedAgent} />;
  } else if (page === 'agent-chat' && selectedAgent) {
    content = <AgentChat agent={selectedAgent} setPage={navigate} setSelectedAgent={setSelectedAgent} />;
  } else if (page === 'agent-detail' && selectedAgent) {
    content = <AgentDetail agent={selectedAgent} setPage={navigate} />;
  } else if (page === 'runs') {
    content = <RunHistory />;
  } else if (page === 'settings') {
    content = <Settings />;
  } else {
    content = <Dashboard setPage={navigate} setSelectedAgent={setSelectedAgent} />;
  }

  return <Layout page={page === 'agent-chat' || page === 'agent-detail' ? 'dashboard' : page} setPage={navigate}>{content}</Layout>;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
