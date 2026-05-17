import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

const inputBase =
  'w-full bg-[#0d1117] border border-[#1f2937] rounded-lg text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/20 transition-colors'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && <label className="block text-xs font-medium text-gray-400">{label}</label>}
      <input ref={ref} className={cn(inputBase, 'px-3 py-2', className)} {...props} />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
)
Input.displayName = 'Input'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, className, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && <label className="block text-xs font-medium text-gray-400">{label}</label>}
      <textarea ref={ref} className={cn(inputBase, 'px-3 py-2 resize-none', className)} {...props} />
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
)
Textarea.displayName = 'Textarea'
