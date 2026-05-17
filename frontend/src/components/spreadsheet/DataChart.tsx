import { useState, useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface DataChartProps {
  headers: string[]
  rows: string[][]
}

type ChartType = 'bar' | 'line' | 'pie'

const COLORS = ['#0ea5e9', '#22d3ee', '#818cf8', '#fb923c', '#34d399', '#f472b6', '#a78bfa', '#fbbf24']

export default function DataChart({ headers, rows }: DataChartProps) {
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [xCol, setXCol] = useState(0)
  const [yCol, setYCol] = useState(1)

  const numericCols = useMemo(
    () => headers.filter((_, i) => rows.some(r => r[i] !== '' && !isNaN(Number(r[i])))),
    [headers, rows]
  )

  const data = useMemo(() => {
    return rows.slice(0, 50).map(row => ({
      name: row[xCol] ?? '',
      value: Number(row[yCol]) || 0,
    }))
  }, [rows, xCol, yCol])

  const select = (value: string, onChange: (i: number) => void) => (
    <select
      value={value}
      onChange={e => onChange(Number(e.target.value))}
      className="bg-[#0d1117] border border-[#1f2937] rounded-lg px-2.5 py-1.5 text-xs text-gray-300 focus:outline-none"
    >
      {headers.map((h, i) => <option key={i} value={i}>{h || `Col ${i + 1}`}</option>)}
    </select>
  )

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 bg-[#0d1117] rounded-lg p-1 border border-[#1f2937]">
          {(['bar', 'line', 'pie'] as ChartType[]).map(t => (
            <button
              key={t}
              onClick={() => setChartType(t)}
              className={cn(
                'px-3 py-1 rounded-md text-xs font-medium transition-all',
                chartType === t ? 'bg-[#111827] text-gray-100' : 'text-gray-500 hover:text-gray-300'
              )}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {chartType !== 'pie' && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>X:</span> {select(String(xCol), setXCol)}
            <span>Y:</span> {select(String(yCol), setYCol)}
          </div>
        )}

        {chartType === 'pie' && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>Value:</span> {select(String(yCol), setYCol)}
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-72 bg-[#0d1117] rounded-xl border border-[#1f2937] p-4">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#d1d5db' }}
                itemStyle={{ color: '#0ea5e9' }}
              />
              <Bar dataKey="value" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : chartType === 'line' ? (
            <LineChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#d1d5db' }}
                itemStyle={{ color: '#0ea5e9' }}
              />
              <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 3, fill: '#0ea5e9' }} />
            </LineChart>
          ) : (
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#6b7280' }} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Column stats */}
      {numericCols.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {numericCols.slice(0, 4).map(col => {
            const ci = headers.indexOf(col)
            const vals = rows.map(r => Number(r[ci])).filter(n => !isNaN(n))
            const min = Math.min(...vals).toFixed(2)
            const max = Math.max(...vals).toFixed(2)
            const mean = (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2)
            return (
              <div key={col} className="bg-[#0d1117] border border-[#1f2937] rounded-lg p-3">
                <p className="text-[11px] font-medium text-gray-400 mb-1.5 truncate">{col}</p>
                <div className="space-y-0.5 text-[11px] text-gray-500">
                  <div className="flex justify-between"><span>Min</span><span className="text-sky-400 font-mono">{min}</span></div>
                  <div className="flex justify-between"><span>Max</span><span className="text-sky-400 font-mono">{max}</span></div>
                  <div className="flex justify-between"><span>Mean</span><span className="text-sky-400 font-mono">{mean}</span></div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
