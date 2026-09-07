'use client'

import { useState } from 'react'
import {
  AudioLines,
  ImageIcon,
  Loader2,
  Pencil,
  RefreshCw,
  TriangleAlert,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import type { Scene } from '@/lib/types'

export interface ScenePatch {
  narration?: string
  onScreenText?: string | null
  audioDuration?: number
}

function statusDot(status: string) {
  switch (status) {
    case 'ready':
      return 'bg-emerald-500'
    case 'generating':
      return 'bg-amber-400 animate-pulse'
    case 'failed':
      return 'bg-red-500'
    default:
      return 'bg-zinc-600'
  }
}

export function SceneCard({
  scene,
  onRegenerate,
  onSave,
  saving,
}: {
  scene: Scene
  onRegenerate: (sceneId: string, target: 'image' | 'audio') => void
  onSave: (sceneId: string, patch: ScenePatch) => Promise<boolean>
  saving: boolean
}) {
  const [editing, setEditing] = useState(false)
  const [narration, setNarration] = useState(scene.narration)
  const [onScreen, setOnScreen] = useState(scene.onScreenText ?? '')

  function startEdit() {
    setNarration(scene.narration)
    setOnScreen(scene.onScreenText ?? '')
    setEditing(true)
  }

  const duration =
    scene.audioDuration ?? scene.subtitles?.duration ?? null

  async function save() {
    const ok = await onSave(scene.id, {
      narration: narration.trim(),
      onScreenText: onScreen.trim() || null,
    })
    if (ok) setEditing(false)
  }

  const imageBusy = scene.imageStatus === 'generating'
  const audioBusy = scene.audioStatus === 'generating'
  const audioStale =
    scene.audioStatus === 'pending' && scene.narration.trim().length > 0

  return (
    <Card className="w-56 shrink-0 border-zinc-800 bg-zinc-900/50 overflow-hidden">
      <CardContent className="p-0">
        <div className="relative aspect-[768/1344] max-h-64 bg-zinc-950 overflow-hidden">
          {scene.imageUrl && scene.imageStatus === 'ready' && (
            <img src={scene.imageUrl} alt={`Scene ${scene.position} visual`} className="h-full w-full object-cover" />
          )}
          {imageBusy && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-zinc-900 animate-pulse">
              <Loader2 className="h-5 w-5 text-amber-400 animate-spin" />
              <span className="text-[11px] text-zinc-400">Rendering image…</span>
            </div>
          )}
          {scene.imageStatus === 'failed' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <TriangleAlert className="h-5 w-5 text-red-400" />
              <span className="text-[11px] text-zinc-400">Image failed</span>
            </div>
          )}
          {scene.imageStatus === 'pending' && !imageBusy && (
            <div className="absolute inset-0 flex items-center justify-center">
              <ImageIcon className="h-6 w-6 text-zinc-700" />
            </div>
          )}
          <span className="absolute top-2 left-2 rounded-md bg-black/70 px-1.5 py-0.5 text-[10px] font-mono text-zinc-200">
            #{scene.position}
          </span>
          {duration != null && (
            <span className="absolute top-2 right-2 rounded-md bg-black/70 px-1.5 py-0.5 text-[10px] font-mono text-zinc-200">
              {duration.toFixed(1)}s
            </span>
          )}
          {scene.onScreenText && !editing && (
            <span className="absolute bottom-2 left-2 right-2 truncate text-[11px] font-bold uppercase tracking-wide text-white drop-shadow-lg">
              {scene.onScreenText}
            </span>
          )}
        </div>

        <div className="p-3 space-y-2.5">
          <div className="flex items-center gap-2 text-[10px] text-zinc-500">
            <span className="flex items-center gap-1">
              <span className={cn('h-1.5 w-1.5 rounded-full', statusDot(scene.imageStatus))} />
              image
            </span>
            <span className="flex items-center gap-1">
              <span className={cn('h-1.5 w-1.5 rounded-full', statusDot(scene.audioStatus))} />
              audio
            </span>
            {scene.imageQuality && (
              <span
                className={cn(
                  'ml-auto font-mono',
                  scene.imageQuality.score >= 6 ? 'text-emerald-400' : 'text-amber-400'
                )}
                title={scene.imageQuality.issue ?? 'Vision QC score'}
              >
                VLM {scene.imageQuality.score}/10
              </span>
            )}
          </div>

          {editing ? (
            <div className="space-y-2">
              <Textarea
                value={narration}
                onChange={(e) => setNarration(e.target.value)}
                rows={3}
                placeholder="Narration (spoken)"
                className="text-xs bg-zinc-950 border-zinc-800 resize-none"
              />
              <Textarea
                value={onScreen}
                onChange={(e) => setOnScreen(e.target.value)}
                rows={1}
                placeholder="On-screen text"
                className="text-xs bg-zinc-950 border-zinc-800 resize-none"
              />
              <div className="flex gap-2">
                <Button size="sm" className="h-7 flex-1" onClick={() => void save()} disabled={saving || !narration.trim()}>
                  {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : null} Save
                </Button>
                <Button size="sm" variant="ghost" className="h-7" onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              </div>
              <p className="text-[10px] text-zinc-500">
                Saving marks the audio stale — regenerate it below.
              </p>
            </div>
          ) : (
            <>
              <p className="text-xs text-zinc-300 line-clamp-4 leading-relaxed">{scene.narration}</p>
              <div className="flex items-center gap-1.5 pt-0.5">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-zinc-400 hover:text-zinc-100"
                  onClick={() => onRegenerate(scene.id, 'image')}
                  disabled={imageBusy}
                  title="Regenerate this scene's image"
                >
                  {imageBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-zinc-400 hover:text-zinc-100"
                  onClick={() => onRegenerate(scene.id, 'audio')}
                  disabled={audioBusy || !scene.narration.trim()}
                  title="Regenerate this scene's narration"
                >
                  {audioBusy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <AudioLines className="h-3.5 w-3.5" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-zinc-400 hover:text-zinc-100 ml-auto"
                  onClick={startEdit}
                  title="Edit narration / on-screen text"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
              </div>
              {(audioStale || scene.audioStatus === 'failed') && (
                <p className="text-[10px] text-amber-400 flex items-center gap-1">
                  <AudioLines className="h-3 w-3" />
                  {scene.audioStatus === 'failed' ? 'Audio failed — regenerate' : 'Audio stale — regenerate after editing'}
                </p>
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
