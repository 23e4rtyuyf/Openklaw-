import { useState } from 'react'
import { Table2, Link2, Upload, BarChart2, Play, Bot } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { sheetsApi } from '../lib/api'
import { Tabs, TabsList, Tab, TabPanel } from '../components/ui/Tabs'
import { Button } from '../components/ui/Button'
import SheetGrid from '../components/spreadsheet/SheetGrid'
import DataChart from '../components/spreadsheet/DataChart'
import CsvUploader from '../components/spreadsheet/CsvUploader'
import SheetConnector from '../components/spreadsheet/SheetConnector'

interface SheetData {
  source: 'csv' | 'google' | 'excel'
  name: string
  headers: string[]
  rows: string[][]
}

export default function Sheets() {
  const [tab, setTab] = useState('connect')
  const [viewTab, setViewTab] = useState('grid')
  const [sheets, setSheets] = useState<SheetData[]>([])
  const [active, setActive] = useState<SheetData | null>(null)
  const [uploadError, setUploadError] = useState('')

  const upload = useMutation({
    mutationFn: sheetsApi.uploadFile,
    onSuccess: (data) => {
      const s: SheetData = {
        source: 'excel',
        name: data.filename,
        headers: data.preview.headers,
        rows: data.preview.rows,
      }
      setSheets(prev => [s, ...prev])
      setActive(s)
      setTab('view')
    },
    onError: (e: Error) => setUploadError(e.message),
  })

  const handleCsvParsed = (filename: string, headers: string[], rows: string[][]) => {
    const s: SheetData = { source: 'csv', name: filename, headers, rows }
    setSheets(prev => [s, ...prev])
    setActive(s)
    setTab('view')
  }

  const handleFileUpload = (file: File) => {
    if (!file.name.endsWith('.csv')) {
      upload.mutate(file)
    }
  }

  const handleGoogleConnected = (headers: string[], rows: string[][], url: string) => {
    const name = `Google Sheet — ${url.slice(-8)}`
    const s: SheetData = { source: 'google', name, headers, rows }
    setSheets(prev => [s, ...prev])
    setActive(s)
    setTab('view')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left panel — sheet list */}
      <aside className="w-56 shrink-0 bg-[#0d1117] border-r border-[#1f2937] flex flex-col">
        <div className="px-4 py-4 border-b border-[#1f2937]">
          <div className="flex items-center gap-2">
            <Table2 size={15} className="text-sky-400" />
            <span className="text-sm font-semibold text-gray-100">Spreadsheets</span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {sheets.length === 0 ? (
            <p className="px-4 py-3 text-xs text-gray-600">No sheets connected yet</p>
          ) : (
            sheets.map((s, i) => (
              <button
                key={i}
                onClick={() => { setActive(s); setTab('view') }}
                className={`w-full text-left px-4 py-2.5 text-xs transition-colors ${
                  active === s ? 'bg-[#1f2937] text-gray-100' : 'text-gray-400 hover:bg-[#111827] hover:text-gray-200'
                }`}
              >
                <div className="font-medium truncate">{s.name}</div>
                <div className="text-[10px] text-gray-600 mt-0.5">{s.rows.length.toLocaleString()} rows · {s.headers.length} cols</div>
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar with tabs */}
        <div className="border-b border-[#1f2937] px-5 py-3 flex items-center gap-3">
          <TabsList>
            <Tab value="connect">
              <span className="flex items-center gap-1.5"><Upload size={12} /> Connect</span>
            </Tab>
            {active && (
              <>
                <Tab value="view">
                  <span className="flex items-center gap-1.5"><Table2 size={12} /> Grid</span>
                </Tab>
                <Tab value="chart">
                  <span className="flex items-center gap-1.5"><BarChart2 size={12} /> Charts</span>
                </Tab>
              </>
            )}
          </TabsList>

          {active && (
            <div className="ml-auto flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium text-gray-300">{active.name}</span>
              <span>·</span>
              <span>{active.rows.length.toLocaleString()} rows</span>
            </div>
          )}
        </div>

        <Tabs value={tab} onChange={setTab}>
          <TabPanel value="connect">
            <div className="p-6 max-w-2xl mx-auto space-y-8 animate-fade-in">
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Link2 size={15} className="text-sky-400" />
                  <h3 className="text-sm font-semibold text-gray-100">Connect Google Sheet</h3>
                </div>
                <SheetConnector onConnected={handleGoogleConnected} />
              </div>

              <div className="border-t border-[#1f2937]" />

              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Upload size={15} className="text-sky-400" />
                  <h3 className="text-sm font-semibold text-gray-100">Upload CSV or Excel</h3>
                </div>
                <CsvUploader onParsed={handleCsvParsed} onFileUpload={handleFileUpload} />
                {upload.isPending && (
                  <p className="text-xs text-gray-500 mt-2 animate-pulse">Uploading and parsing...</p>
                )}
                {uploadError && <p className="text-xs text-red-400 mt-2">{uploadError}</p>}
              </div>
            </div>
          </TabPanel>

          {active && (
            <TabPanel value="view">
              <div className="flex-1 h-[calc(100vh-105px)] overflow-hidden">
                <SheetGrid headers={active.headers} rows={active.rows} filename={active.name} />
              </div>
            </TabPanel>
          )}

          {active && (
            <TabPanel value="chart">
              <div className="p-6 max-w-4xl">
                <DataChart headers={active.headers} rows={active.rows} />
              </div>
            </TabPanel>
          )}
        </Tabs>
      </div>
    </div>
  )
}
