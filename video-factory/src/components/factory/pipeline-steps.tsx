'use client'

import {
  AudioLines,
  Check,
  Loader2,
  PenLine,
  Search,
  ShieldCheck,
  ImageIcon,
  Type,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { PipelineEventDTO, Project } from '@/lib/types'

const STEP_ICONS = [Search, PenLine, ImageIcon, AudioLines, Type, ShieldCheck]

type StepState = 'pending' | 'active' | 'done' | 'warning' | 'error'

function stepState(project: Project, stepId: string): StepState {
  const scenes = project.scenes
  switch (stepId) {
    case 'research':
      if (project.research) return 'done'
      return project.status === 'researching' ? 'active' : 'pending'
    case 'script':
      if (scenes.length > 0) return 'done'
      return project.status === 'scripting' ? 'active' : 'pending'
    case 'visuals': {
      const ready = scenes.filter((s) => s.imageStatus === 'ready').length
      if (ready === scenes.length && scenes.length > 0) return 'done'
      if (scenes.some((s) => s.imageStatus === 'failed')) return 'error'
      if (scenes.some((s) => s.imageStatus === 'generating') || project.status === 'visualizing')
        return 'active'
      return 'pending'
    }
    case 'narration': {
      const ready = scenes.filter((s) => s.audioStatus === 'ready').length
      if (ready === scenes.length && scenes.length > 0) return 'done'
      if (scenes.some((s) => s.audioStatus === 'failed')) return 'error'
      if (scenes.some((s) => s.audioStatus === 'generating') || project.status === 'narrating')
        return 'active'
      return 'pending'
    }
    case 'captions': {
      const withTracks = scenes.filter((s) => s.subtitles).length
      if (scenes.length > 0 && withTracks === scenes.length) return 'done'
      return project.status === 'subtitling' ? 'active' : 'pending'
    }
    case 'quality':
      if (project.quality) return project.quality.passed ? 'done' : 'warning'
      return project.status === 'quality_review' ? 'active' : 'pending'
    default:
      return 'pending'
  }
}

function StepIcon({ state, Icon }: { state: StepState; Icon: typeof Search }) {
  return (
    <span
      className={cn(
        'flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs',
        state === 'pending' && 'border-zinc-700 bg-zinc-900 text-zinc-500',
        state === 'active' && 'border-amber-500/50 bg-amber-500/15 text-amber-400',
        state === 'done' && 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
        state === 'warning' && 'border-amber-500/40 bg-amber-500/10 text-amber-400',
        state === 'error' && 'border-red-500/40 bg-red-500/10 text-red-400'
      )}
    >
      {state === 'active' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Icon className="h-3.5 w-3.5" />}
    </span>
  )
}

function StepCheck({ state }: { state: StepState }) {
  if (state === 'done') return <Check className="h-3.5 w-3.5 text-emerald-400" />
  if (state === 'warning') return <span className="text-amber-400 text-xs">!</span>
  if (state === 'error') return <span className="text-red-400 text-xs">×</span>
  return null
}

export function PipelineSteps({ project }: { project: Project }) {
  const steps = ['research', 'script', 'visuals', 'narration', 'captions', 'quality']
  const labels: Record<string, string> = {
    research: 'Research',
    script: 'Script',
    visuals: 'Visuals',
    narration: 'Narration',
    captions: 'Captions',
    quality: 'Quality gate',
  }

  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          Pipeline
          {project.stepDetail && (
            <span className="text-xs font-normal text-amber-400 truncate">{project.stepDetail}</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-2.5">
          {steps.map((stepId, i) => {
            const state = stepState(project, stepId)
            const Icon = STEP_ICONS[i]
            return (
              <li key={stepId} className="flex items-center gap-3">
                <StepIcon state={state} Icon={Icon} />
                <span
                  className={cn(
                    'text-sm flex-1',
                    state === 'pending' ? 'text-zinc-500' : 'text-zinc-200'
                  )}
                >
                  {labels[stepId]}
                </span>
                {state === 'active' && <span className="text-xs text-amber-400">running…</span>}
                <StepCheck state={state} />
              </li>
            )
          })}
        </ol>

        <div>
          <p className="text-xs uppercase tracking-wide text-zinc-500 mb-1.5">Activity log</p>
          <div className="max-h-40 overflow-y-auto scrollbar-slim rounded-md border border-zinc-800 bg-zinc-950 p-2 space-y-1">
            {project.events.length === 0 && (
              <p className="text-xs text-zinc-600 px-1">Waiting for events…</p>
            )}
            {project.events.slice(0, 20).map((e) => (
              <EventLine key={e.id} event={e} />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function EventLine({ event }: { event: PipelineEventDTO }) {
  return (
    <div className="flex items-start gap-2 text-[11px] leading-relaxed">
      <span
        className={cn(
          'mt-1 h-1.5 w-1.5 shrink-0 rounded-full',
          event.status === 'running' && 'bg-amber-400',
          event.status === 'done' && 'bg-emerald-400',
          event.status === 'warning' && 'bg-amber-500',
          event.status === 'failed' && 'bg-red-400',
          event.status === 'skipped' && 'bg-zinc-500'
        )}
      />
      <span className="text-zinc-500 font-mono shrink-0">
        {new Date(event.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
      </span>
      <span className="text-zinc-400">{event.message}</span>
    </div>
  )
}
