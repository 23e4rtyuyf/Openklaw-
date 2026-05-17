import { cn, statusBg } from '../../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'status' | 'default' | 'blue' | 'purple' | 'orange'
  status?: string
  className?: string
}

const variantStyles = {
  default: 'bg-gray-500/10 text-gray-400',
  blue: 'bg-sky-500/10 text-sky-400',
  purple: 'bg-violet-500/10 text-violet-400',
  orange: 'bg-orange-500/10 text-orange-400',
  status: '',
}

export function Badge({ children, variant = 'default', status, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'tag',
        variant === 'status' && status ? statusBg(status) : variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
