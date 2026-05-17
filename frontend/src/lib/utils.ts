import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function timeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function extractSheetId(url: string): string | null {
  const m = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/)
  return m ? m[1] : null
}

export function statusColor(status: string): string {
  switch (status) {
    case 'success': return 'text-emerald-400'
    case 'running': return 'text-sky-400'
    case 'error':
    case 'failed': return 'text-red-400'
    case 'active': return 'text-emerald-400'
    default: return 'text-gray-400'
  }
}

export function statusBg(status: string): string {
  switch (status) {
    case 'success': return 'bg-emerald-500/10 text-emerald-400'
    case 'running': return 'bg-sky-500/10 text-sky-400'
    case 'error':
    case 'failed': return 'bg-red-500/10 text-red-400'
    case 'active': return 'bg-emerald-500/10 text-emerald-400'
    case 'inactive': return 'bg-gray-500/10 text-gray-400'
    default: return 'bg-gray-500/10 text-gray-400'
  }
}
