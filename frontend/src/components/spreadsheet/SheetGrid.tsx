import { useState, useMemo } from 'react'
import {
  useReactTable, getCoreRowModel, getSortedRowModel, getFilteredRowModel,
  getPaginationRowModel, flexRender, type SortingState, type ColumnDef,
} from '@tanstack/react-table'
import { ChevronUp, ChevronDown, ChevronsUpDown, Download, Search } from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface SheetGridProps {
  headers: string[]
  rows: string[][]
  filename?: string
}

export default function SheetGrid({ headers, rows, filename }: SheetGridProps) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')

  const columns = useMemo<ColumnDef<string[]>[]>(
    () =>
      headers.map((h, i) => ({
        id: h || `col_${i}`,
        header: h || `Column ${i + 1}`,
        accessorFn: (row: string[]) => row[i] ?? '',
        cell: (info) => {
          const v = info.getValue() as string
          const isNum = v !== '' && !isNaN(Number(v))
          return (
            <span className={cn('text-xs', isNum ? 'text-sky-300 font-mono' : 'text-gray-300')}>
              {v}
            </span>
          )
        },
      })),
    [headers]
  )

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  })

  const exportCsv = () => {
    const lines = [headers.join(','), ...rows.map(r => r.map(c => `"${c}"`).join(','))]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename?.replace(/\.[^.]+$/, '') + '.csv' || 'export.csv'
    a.click()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#1f2937]">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={globalFilter}
              onChange={e => setGlobalFilter(e.target.value)}
              placeholder="Filter..."
              className="pl-7 pr-3 py-1.5 bg-[#0d1117] border border-[#1f2937] rounded-lg text-xs text-gray-300 placeholder-gray-500 focus:outline-none focus:border-sky-500/50 w-48"
            />
          </div>
          <span className="text-xs text-gray-500">
            {table.getFilteredRowModel().rows.length.toLocaleString()} rows · {headers.length} cols
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={exportCsv}>
          <Download size={13} /> Export CSV
        </Button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm border-collapse">
          <thead className="sticky top-0 bg-[#0d1117] z-10">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                <th className="w-10 text-right pr-3 py-2 text-[11px] text-gray-600 font-mono border-b border-[#1f2937]">#</th>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-3 py-2 text-left text-[11px] font-medium text-gray-400 border-b border-[#1f2937] cursor-pointer select-none hover:text-gray-200 whitespace-nowrap"
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && <ChevronUp size={10} className="text-sky-400" />}
                      {header.column.getIsSorted() === 'desc' && <ChevronDown size={10} className="text-sky-400" />}
                      {!header.column.getIsSorted() && <ChevronsUpDown size={10} className="opacity-0 group-hover:opacity-100" />}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, ri) => (
              <tr key={row.id} className="hover:bg-[#111827] group transition-colors">
                <td className="text-right pr-3 py-1.5 text-[11px] text-gray-600 font-mono border-b border-[#1f2937]/50">
                  {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + ri + 1}
                </td>
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-3 py-1.5 border-b border-[#1f2937]/50 max-w-[200px] truncate">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-[#1f2937] text-xs text-gray-500">
          <span>Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}</span>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Prev</Button>
            <Button variant="ghost" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}
