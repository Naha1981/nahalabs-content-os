'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  ExternalLink,
  Hash,
  RefreshCw,
  Wand2,
} from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { PLATFORMS } from '@/lib/types'
import type { Project, Scene } from '@/lib/types'
import { PipelineSteps } from './pipeline-steps'
import { QualityReportCard } from './quality-report'
import { SceneCard, type ScenePatch } from './scene-card'
import { StatusBadge } from './status-badge'
import { VideoPlayer } from './video-player'

export function ProjectView({
  project,
  onBack,
  onRun,
  onRegenerateScene,
  onPatchScene,
  runBusy,
  sceneSaving,
}: {
  project: Project
  onBack: () => void
  onRun: (id: string) => void
  onRegenerateScene: (sceneId: string, target: 'image' | 'audio') => void
  onPatchScene: (sceneId: string, patch: ScenePatch) => Promise<Scene | null>
  runBusy: boolean
  sceneSaving: boolean
}) {
  const [researchOpen, setResearchOpen] = useState(false)
  const platformLabel = PLATFORMS.find((p) => p.value === project.platform)?.label ?? project.platform

  const hasFailedAssets = project.scenes.some(
    (s) => s.imageStatus === 'failed' || s.audioStatus === 'failed'
  )
  const showRun =
    hasFailedAssets ||
    project.status === 'failed' ||
    project.status === 'quality_failed'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <Button variant="ghost" size="sm" onClick={onBack} className="text-zinc-400">
          <ArrowLeft className="h-4 w-4" /> All videos
        </Button>
        <StatusBadge status={project.status} />
        <Badge variant="outline" className="border-zinc-700 text-zinc-400">
          {platformLabel}
        </Badge>
        <Badge variant="outline" className="border-zinc-700 text-zinc-400">
          {project.mode === 'ugc' ? 'UGC ad' : 'Topic video'}
        </Badge>
        <Badge variant="outline" className="border-zinc-700 text-zinc-400">
          {project.durationTarget}s target
        </Badge>
        {showRun && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRun(project.id)}
            disabled={runBusy}
            className="ml-auto border-amber-500/40 text-amber-400 hover:text-amber-300"
          >
            {runBusy ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
            Resume / fix
          </Button>
        )}
      </div>

      {project.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Pipeline error</AlertTitle>
          <AlertDescription>{project.error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,400px)_minmax(0,1fr)] items-start">
        <VideoPlayer project={project} onSceneDuration={handleSceneDuration} />

        <div className="space-y-6">
          <PipelineSteps project={project} />
          {project.quality && <QualityReportCard report={project.quality} />}
          <ScriptCard project={project} researchOpen={researchOpen} setResearchOpen={setResearchOpen} />
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-sm font-semibold text-zinc-200">Storyboard</h2>
          <span className="text-xs text-zinc-500">
            {project.scenes.length} scenes — edit, regenerate, reorder mentally, re-render
          </span>
        </div>
        {project.scenes.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
            Scenes appear here once the script step finishes.
          </div>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-3 scrollbar-slim">
            {project.scenes.map((scene) => (
              <SceneCard
                key={scene.id}
                scene={scene}
                onRegenerate={onRegenerateScene}
                onSave={async (id, patch) => {
                  const updated = await onPatchScene(id, patch)
                  return updated != null
                }}
                saving={sceneSaving}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )

  async function handleSceneDuration(sceneId: string, duration: number) {
    await onPatchScene(sceneId, { audioDuration: duration })
  }
}

function ScriptCard({
  project,
  researchOpen,
  setResearchOpen,
}: {
  project: Project
  researchOpen: boolean
  setResearchOpen: (v: boolean) => void
}) {
  const script = project.script
  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Script</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {script ? (
          <>
            <div className="space-y-2">
              {script.hook && (
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">Hook</p>
                  <p className="text-sm text-zinc-200">{script.hook}</p>
                </div>
              )}
              {script.cta && (
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">CTA</p>
                  <p className="text-sm text-zinc-200">{script.cta}</p>
                </div>
              )}
              {script.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {script.hashtags.map((h) => (
                    <span
                      key={h}
                      className="inline-flex items-center gap-0.5 rounded-full border border-zinc-700 bg-zinc-800/60 px-2 py-0.5 text-[11px] text-zinc-300"
                    >
                      <Hash className="h-2.5 w-2.5" />
                      {h.replace(/^#/, '')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <p className="text-sm text-zinc-500">Script generates after research completes.</p>
        )}

        {project.research && (
          <Collapsible open={researchOpen} onOpenChange={setResearchOpen}>
            <CollapsibleTrigger className="flex w-full items-center justify-between text-xs text-zinc-400 hover:text-zinc-200">
              <span>Research brief ({project.research.sources.length} sources)</span>
              <ChevronDown className={`h-3.5 w-3.5 transition-transform ${researchOpen ? 'rotate-180' : ''}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-3 pt-3">
              <p className="text-xs text-zinc-300 leading-relaxed">{project.research.summary}</p>
              {project.research.keyPoints.length > 0 && (
                <ul className="space-y-1 list-disc pl-4">
                  {project.research.keyPoints.map((k, i) => (
                    <li key={i} className="text-xs text-zinc-400">{k}</li>
                  ))}
                </ul>
              )}
              {project.research.hooks.length > 0 && (
                <div>
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500 mb-1">Hook options</p>
                  <ul className="space-y-1">
                    {project.research.hooks.map((h, i) => (
                      <li key={i} className="text-xs text-zinc-400">“{h}”</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {project.research.sources.map((s, i) => (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-amber-400/80 hover:text-amber-300 truncate max-w-[240px]"
                  >
                    <ExternalLink className="h-3 w-3 shrink-0" />
                    <span className="truncate">{s.title}</span>
                  </a>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  )
}
