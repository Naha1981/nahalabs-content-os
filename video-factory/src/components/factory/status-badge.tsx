import { cn } from '@/lib/utils'
import { statusLabel, type ProjectStatus } from '@/lib/types'

const ACTIVE: ProjectStatus[] = [
  'queued',
  'researching',
  'scripting',
  'visualizing',
  'narrating',
  'subtitling',
  'quality_review',
]

export function StatusBadge({ status, className }: { status: ProjectStatus; className?: string }) {
  const isActive = ACTIVE.includes(status)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        status === 'approved_ready' && 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
        status === 'quality_failed' && 'border-amber-500/40 bg-amber-500/10 text-amber-400',
        status === 'failed' && 'border-red-500/40 bg-red-500/10 text-red-400',
        isActive && 'border-amber-500/40 bg-amber-500/10 text-amber-300',
        status === 'queued' && 'border-zinc-700 bg-zinc-800/60 text-zinc-300',
        className
      )}
    >
      {isActive && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-400" />
        </span>
      )}
      {statusLabel(status)}
    </span>
  )
}
