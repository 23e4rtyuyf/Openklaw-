import { createContext, useContext, type ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface TabsContextValue {
  value: string
  onChange: (v: string) => void
}

const TabsCtx = createContext<TabsContextValue>({ value: '', onChange: () => {} })

export function Tabs({ value, onChange, children }: TabsContextValue & { children: ReactNode }) {
  return <TabsCtx.Provider value={{ value, onChange }}>{children}</TabsCtx.Provider>
}

export function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('flex gap-1 bg-[#0d1117] rounded-lg p-1 border border-[#1f2937]', className)}>
      {children}
    </div>
  )
}

export function Tab({ value, children }: { value: string; children: ReactNode }) {
  const ctx = useContext(TabsCtx)
  return (
    <button
      onClick={() => ctx.onChange(value)}
      className={cn(
        'px-3.5 py-1.5 rounded-md text-sm font-medium transition-all duration-150',
        ctx.value === value
          ? 'bg-[#111827] text-gray-100 shadow'
          : 'text-gray-500 hover:text-gray-300'
      )}
    >
      {children}
    </button>
  )
}

export function TabPanel({ value, children }: { value: string; children: ReactNode }) {
  const ctx = useContext(TabsCtx)
  if (ctx.value !== value) return null
  return <div>{children}</div>
}
