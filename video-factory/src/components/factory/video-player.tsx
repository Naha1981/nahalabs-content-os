'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Braces,
  Captions,
  Code2,
  Film,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  Volume2,
  VolumeX,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { useToast } from '@/hooks/use-toast'
import { cueGroups, estimateDuration } from '@/lib/subtitles'
import type { Project, Scene, WordTiming } from '@/lib/types'
import { downloadBlob, downloadUrl, formatClock, slugify } from '@/lib/client-utils'

const W = 768
const H = 1344
const FADE = 0.5

interface TimelineEntry {
  scene: Scene
  start: number
  duration: number
}

export function VideoPlayer({
  project,
  onSceneDuration,
}: {
  project: Project
  onSceneDuration?: (sceneId: string, duration: number) => void
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { toast } = useToast()

  const onDurRef = useRef(onSceneDuration)
  useEffect(() => {
    onDurRef.current = onSceneDuration
  }, [onSceneDuration])

  const playable = useMemo(
    () => project.scenes.filter((s) => s.imageUrl || s.audioUrl),
    [project.scenes]
  )

  const durationsRef = useRef<Map<string, number>>(new Map())
  const [durationVersion, setDurationVersion] = useState(0)

  const timeline = useMemo(() => {
    let acc = 0
    const list: TimelineEntry[] = playable.map((scene) => {
      const dur =
        durationsRef.current.get(scene.id) ??
        scene.audioDuration ??
        scene.subtitles?.duration ??
        estimateDuration(scene.narration)
      const entry = { scene, start: acc, duration: Math.max(0.4, dur) }
      acc += entry.duration
      return entry
    })
    void durationVersion
    return { list, total: acc }
  }, [playable, durationVersion])

  // ---- asset caches -------------------------------------------------------
  const imagesRef = useRef<Map<string, HTMLImageElement>>(new Map())
  const audioRef = useRef<Map<string, HTMLAudioElement>>(new Map())

  const assetKey = useMemo(
    () => playable.map((s) => `${s.id}:${s.imageUrl ?? ''}:${s.audioUrl ?? ''}`).join('|'),
    [playable]
  )

  const [assetsReady, setAssetsReady] = useState(false)
  const [loadProgress, setLoadProgress] = useState({ done: 0, total: 0 })

  useEffect(() => {
    let cancelled = false
    const withImg = playable.filter((s) => s.imageUrl)
    const withAudio = playable.filter((s) => s.audioUrl)
    const total = withImg.length + withAudio.length
    setAssetsReady(total === 0)
    setLoadProgress({ done: 0, total })
    let done = 0
    const bump = () => {
      done++
      if (!cancelled) setLoadProgress({ done, total })
    }

    const imageJobs = withImg.map(
      (s) =>
        new Promise<void>((resolve) => {
          const url = s.imageUrl as string
          if (imagesRef.current.has(url)) {
            bump()
            resolve()
            return
          }
          const img = new Image()
          img.onload = () => {
            imagesRef.current.set(url, img)
            bump()
            resolve()
          }
          img.onerror = () => {
            bump()
            resolve()
          }
          img.src = url
        })
    )

    const audioJobs = withAudio.map(
      (s) =>
        new Promise<void>((resolve) => {
          if (audioRef.current.has(s.id)) {
            bump()
            resolve()
            return
          }
          const a = new Audio()
          a.preload = 'auto'
          a.src = s.audioUrl as string
          let settled = false
          const finish = () => {
            if (settled) return
            settled = true
            audioRef.current.set(s.id, a)
            const d = a.duration
            if (Number.isFinite(d) && d > 0) {
              const prev = durationsRef.current.get(s.id)
              if (prev == null || Math.abs(prev - d) > 0.05) {
                durationsRef.current.set(s.id, d)
                setDurationVersion((v) => v + 1)
                onDurRef.current?.(s.id, d)
              }
            }
            bump()
            resolve()
          }
          a.addEventListener('loadedmetadata', finish, { once: true })
          a.addEventListener('error', finish, { once: true })
          a.load()
          setTimeout(finish, 8000)
        })
    )

    void Promise.all([...imageJobs, ...audioJobs]).then(() => {
      if (!cancelled) setAssetsReady(true)
    })
    return () => {
      cancelled = true
    }
  }, [assetKey])

  // ---- playback state -----------------------------------------------------
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(false)
  const [time, setTime] = useState(0)
  const [exporting, setExporting] = useState(false)

  const timeRef = useRef(0)
  const clockRef = useRef({ base: 0, startedAt: 0 })
  const rafRef = useRef(0)
  const lastUiRef = useRef(0)
  const activeAudioRef = useRef<string | null>(null)
  const mutedRef = useRef(false)
  const finishRef = useRef<(() => void) | null>(null)
  const exportingRef = useRef(false)

  // ---- drawing ------------------------------------------------------------
  const drawFrame = useCallback(
    (t: number) => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.fillStyle = '#09090b'
      ctx.fillRect(0, 0, W, H)

      const { list, total } = timeline
      if (list.length === 0) {
        drawIdle(ctx)
        return
      }
      const clamped = Math.max(0, Math.min(t, total))
      let idx = list.findIndex((e) => clamped >= e.start && clamped < e.start + e.duration)
      if (idx === -1) idx = clamped >= total ? list.length - 1 : 0
      const entry = list[idx]
      const local = clamped - entry.start
      drawScene(ctx, entry, local, idx)
      const next = list[idx + 1]
      if (next && entry.duration - local < FADE) {
        const alpha = 1 - (entry.duration - local) / FADE
        drawScene(ctx, next, 0.001, idx + 1, alpha)
      }
    },
    [timeline]
  )

  function drawIdle(ctx: CanvasRenderingContext2D) {
    ctx.fillStyle = '#71717a'
    ctx.font = '600 30px system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('Storyboard fills in as the pipeline runs…', W / 2, H / 2)
    ctx.textAlign = 'left'
  }

  function drawScene(
    ctx: CanvasRenderingContext2D,
    entry: TimelineEntry,
    local: number,
    idx: number,
    alpha = 1
  ) {
    const scene = entry.scene
    const img = scene.imageUrl ? imagesRef.current.get(scene.imageUrl) : undefined
    const p = Math.max(0, Math.min(1, local / Math.max(0.001, entry.duration)))

    ctx.save()
    ctx.globalAlpha = alpha
    if (img && img.complete && img.naturalWidth > 0) {
      const zoom = 1.07 + 0.1 * p
      const panX = (idx % 2 === 0 ? -1 : 1) * 30 * p
      const panY = (idx % 3 === 0 ? 1 : -1) * 18 * p
      const scale = Math.max(W / img.naturalWidth, H / img.naturalHeight) * zoom
      const dw = img.naturalWidth * scale
      const dh = img.naturalHeight * scale
      ctx.drawImage(img, (W - dw) / 2 + panX, (H - dh) / 2 + panY, dw, dh)
    } else {
      ctx.fillStyle = '#18181b'
      ctx.fillRect(0, 0, W, H)
    }

    // readability gradients
    const top = ctx.createLinearGradient(0, 0, 0, 380)
    top.addColorStop(0, 'rgba(0,0,0,0.6)')
    top.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.fillStyle = top
    ctx.fillRect(0, 0, W, 380)
    const bottom = ctx.createLinearGradient(0, H - 520, 0, H)
    bottom.addColorStop(0, 'rgba(0,0,0,0)')
    bottom.addColorStop(1, 'rgba(0,0,0,0.75)')
    ctx.fillStyle = bottom
    ctx.fillRect(0, H - 520, W, 520)

    if (scene.onScreenText) drawOnScreenText(ctx, scene.onScreenText)
    if (scene.subtitles && scene.subtitles.words.length > 0) {
      drawKaraoke(ctx, scene.subtitles.words, local)
    }
    ctx.restore()
  }

  function drawOnScreenText(ctx: CanvasRenderingContext2D, text: string) {
    const fontSize = 74
    ctx.font = `800 ${fontSize}px system-ui, sans-serif`
    ctx.textBaseline = 'alphabetic'
    const maxW = W - 140
    const spaceW = ctx.measureText(' ').width
    const words = text.split(/\s+/).filter(Boolean)
    const lines: { words: string[]; width: number }[] = []
    let cur: string[] = []
    let curW = 0
    for (const w of words) {
      const ww = ctx.measureText(w).width
      if (cur.length > 0 && curW + spaceW + ww > maxW) {
        lines.push({ words: cur, width: curW })
        cur = []
        curW = 0
      }
      curW += (cur.length ? spaceW : 0) + ww
      cur.push(w)
    }
    if (cur.length) lines.push({ words: cur, width: curW })

    let y = 200
    for (const line of lines) {
      let x = (W - line.width) / 2
      ctx.fillStyle = '#ffffff'
      ctx.shadowColor = 'rgba(0,0,0,0.85)'
      ctx.shadowBlur = 24
      for (const w of line.words) {
        ctx.fillText(w, x, y)
        x += ctx.measureText(w).width + spaceW
      }
      y += fontSize * 1.18
    }
    ctx.shadowBlur = 0
  }

  function drawKaraoke(ctx: CanvasRenderingContext2D, words: WordTiming[], local: number) {
    const groups = cueGroups(words, 5)
    let cue: WordTiming[] | null = null
    for (const g of groups) {
      if (local >= g[0].s - 0.15 && local <= g[g.length - 1].e + 0.3) {
        cue = g
        break
      }
    }
    if (!cue) return

    const fontSize = 58
    ctx.font = `700 ${fontSize}px system-ui, sans-serif`
    const maxW = W - 120
    const spaceW = ctx.measureText(' ').width
    const lines: { words: WordTiming[]; width: number }[] = []
    let cur: WordTiming[] = []
    let curW = 0
    for (const w of cue) {
      const ww = ctx.measureText(w.w).width
      if (cur.length > 0 && curW + spaceW + ww > maxW) {
        lines.push({ words: cur, width: curW })
        cur = []
        curW = 0
      }
      curW += (cur.length ? spaceW : 0) + ww
      cur.push(w)
    }
    if (cur.length) lines.push({ words: cur, width: curW })

    const lineH = fontSize * 1.25
    const blockH = lines.length * lineH
    const blockW = Math.max(...lines.map((l) => l.width))
    const baseY = H - 170 - blockH + fontSize
    const padX = 30
    const padY = 22

    // caption backdrop
    ctx.save()
    ctx.fillStyle = 'rgba(0,0,0,0.5)'
    const bx = (W - blockW) / 2 - padX
    const by = baseY - fontSize - padY + 6
    const bw = blockW + padX * 2
    const bh = blockH + padY * 2 - 12
    const r = 24
    ctx.beginPath()
    ctx.moveTo(bx + r, by)
    ctx.lineTo(bx + bw - r, by)
    ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + r)
    ctx.lineTo(bx + bw, by + bh - r)
    ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - r, by + bh)
    ctx.lineTo(bx + r, by + bh)
    ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - r)
    ctx.lineTo(bx, by + r)
    ctx.quadraticCurveTo(bx, by, bx + r, by)
    ctx.fill()

    let y = baseY
    for (const line of lines) {
      let x = (W - line.width) / 2
      for (const w of line.words) {
        const active = local >= w.s && local <= w.e
        if (active) {
          ctx.fillStyle = '#fbbf24'
          ctx.shadowColor = 'rgba(251,191,36,0.95)'
          ctx.shadowBlur = 20
        } else {
          ctx.fillStyle = '#f4f4f5'
          ctx.shadowColor = 'rgba(0,0,0,0.9)'
          ctx.shadowBlur = 6
        }
        ctx.fillText(w.w, x, y)
        x += ctx.measureText(w.w).width + spaceW
      }
      y += lineH
    }
    ctx.restore()
  }

  // draw current frame whenever timeline/assets change
  useEffect(() => {
    drawFrame(timeRef.current)
  }, [drawFrame, assetsReady])

  // ---- playback loop ------------------------------------------------------
  const entryAt = useCallback(
    (t: number): TimelineEntry | null => {
      const { list } = timeline
      for (const e of list) {
        if (t >= e.start && t < e.start + e.duration) return e
      }
      return list.length > 0 ? list[list.length - 1] : null
    },
    [timeline]
  )

  const syncAudio = useCallback(
    (t: number) => {
      const entry = entryAt(t)
      if (!entry || !entry.scene.audioUrl) {
        if (activeAudioRef.current) {
          const prev = audioRef.current.get(activeAudioRef.current)
          prev?.pause()
          activeAudioRef.current = null
        }
        return
      }
      const el = audioRef.current.get(entry.scene.id)
      if (!el) return
      if (activeAudioRef.current !== entry.scene.id) {
        for (const [, a] of audioRef.current) {
          if (a !== el) a.pause()
        }
        activeAudioRef.current = entry.scene.id
        try {
          el.currentTime = Math.max(0, t - entry.start)
        } catch {
          /* seek before metadata */
        }
        el.muted = mutedRef.current
        void el.play().catch(() => undefined)
      } else {
        const drift = (t - entry.start) - el.currentTime
        if (Math.abs(drift) > 0.4) {
          try {
            el.currentTime = t - entry.start
          } catch {
            /* ignore */
          }
        }
      }
    },
    [entryAt]
  )

  const stopAudio = useCallback(() => {
    for (const [, a] of audioRef.current) a.pause()
    activeAudioRef.current = null
  }, [])

  const tick = useCallback(() => {
    const t = clockRef.current.base + (performance.now() - clockRef.current.startedAt) / 1000
    const { total } = timeline
    if (t >= total) {
      timeRef.current = total
      setTime(total)
      drawFrame(total)
      setPlaying(false)
      stopAudio()
      const finish = finishRef.current
      finishRef.current = null
      finish?.()
      return
    }
    timeRef.current = t
    if (t - lastUiRef.current >= 0.1) {
      lastUiRef.current = t
      setTime(t)
    }
    syncAudio(t)
    drawFrame(t)
    rafRef.current = requestAnimationFrame(tick)
  }, [timeline, drawFrame, syncAudio, stopAudio])

  const play = useCallback(() => {
    if (timeline.total <= 0) return
    let from = timeRef.current
    if (from >= timeline.total - 0.05) {
      from = 0
      timeRef.current = 0
    }
    clockRef.current = { base: from, startedAt: performance.now() }
    lastUiRef.current = from
    setTime(from)
    activeAudioRef.current = null // force audio re-pick
    setPlaying(true)
    rafRef.current = requestAnimationFrame(tick)
  }, [timeline, tick])

  const pause = useCallback(() => {
    cancelAnimationFrame(rafRef.current)
    setPlaying(false)
    clockRef.current = { base: timeRef.current, startedAt: performance.now() }
    stopAudio()
  }, [stopAudio])

  const seek = useCallback(
    (t: number) => {
      const clamped = Math.max(0, Math.min(t, timeline.total))
      timeRef.current = clamped
      lastUiRef.current = clamped
      setTime(clamped)
      clockRef.current = { base: clamped, startedAt: performance.now() }
      stopAudio()
      activeAudioRef.current = null
      drawFrame(clamped)
      if (playing) syncAudio(clamped)
    },
    [timeline, drawFrame, playing, syncAudio, stopAudio]
  )

  const restart = useCallback(() => {
    timeRef.current = 0
    setTime(0)
    clockRef.current = { base: 0, startedAt: performance.now() }
    stopAudio()
    activeAudioRef.current = null
    drawFrame(0)
    if (!playing) play()
    else syncAudio(0)
  }, [playing, play, syncAudio, drawFrame, stopAudio])

  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current)
    }
  }, [])

  // ---- WebM export (real-time canvas + audio capture) ---------------------
  const audioGraphRef = useRef<{
    ctx: AudioContext
    dest: MediaStreamAudioDestinationNode
  } | null>(null)

  const ensureAudioGraph = useCallback(async () => {
    if (audioGraphRef.current) {
      await audioGraphRef.current.ctx.resume().catch(() => undefined)
      return audioGraphRef.current
    }
    const ctx = new AudioContext()
    const dest = ctx.createMediaStreamDestination()
    for (const [id, el] of audioRef.current) {
      if (!el.src) continue
      try {
        const source = ctx.createMediaElementSource(el)
        const gain = ctx.createGain()
        gain.gain.value = mutedRef.current ? 0 : 1
        source.connect(gain)
        gain.connect(dest)
        gain.connect(ctx.destination)
        ;(el as HTMLAudioElement & { __vfGain?: GainNode }).__vfGain = gain
        void id
      } catch {
        // element already connected or unavailable
      }
    }
    audioGraphRef.current = { ctx, dest }
    await ctx.resume().catch(() => undefined)
    return audioGraphRef.current
  }, [])

  async function exportWebM() {
    if (!assetsReady || timeline.total <= 0 || exportingRef.current) return
    exportingRef.current = true
    try {
      const graph = await ensureAudioGraph()
      const canvas = canvasRef.current
      if (!canvas) throw new Error('Canvas unavailable')
      const stream = canvas.captureStream(30)
      const mixed = new MediaStream([
        ...stream.getVideoTracks(),
        ...graph.dest.stream.getAudioTracks(),
      ])
      const mimes = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
      ]
      const mimeType = mimes.find((m) => MediaRecorder.isTypeSupported(m))
      const rec = new MediaRecorder(
        mixed,
        mimeType
          ? { mimeType, videoBitsPerSecond: 5_000_000, audioBitsPerSecond: 128_000 }
          : undefined
      )
      const chunks: Blob[] = []
      rec.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }
      const stopped = new Promise<void>((resolve) => {
        rec.onstop = () => resolve()
      })

      setExporting(true)
      rec.start(500)
      seek(0)
      await new Promise<void>((resolve) => {
        finishRef.current = resolve
        play()
      })
      await new Promise((r) => setTimeout(r, 300))
      rec.stop()
      await stopped

      const blob = new Blob(chunks, { type: mimeType ?? 'video/webm' })
      const name = `${slugify(project.title)}.webm`
      downloadBlob(blob, name)
      toast({
        title: 'Video exported',
        description: `${name} — ${timeline.total.toFixed(0)}s, rendered in real time`,
      })
    } catch (err) {
      toast({
        title: 'Export failed',
        description: (err as Error).message,
        variant: 'destructive',
      })
    } finally {
      setExporting(false)
      exportingRef.current = false
    }
  }

  function toggleMute() {
    const next = !mutedRef.current
    mutedRef.current = next
    setMuted(next)
    for (const [, el] of audioRef.current) {
      el.muted = next
      const gain = (el as HTMLAudioElement & { __vfGain?: GainNode }).__vfGain
      if (gain) gain.gain.value = next ? 0 : 1
    }
  }

  const exportDisabled = !assetsReady || timeline.total <= 0 || exporting

  async function handleDownload(format: 'srt' | 'json' | 'remotion') {
    try {
      const ext = format === 'json' ? 'json' : format === 'srt' ? 'srt' : 'tsx'
      await downloadUrl(`/api/projects/${project.id}/export?format=${format}`, `${slugify(project.title)}.${ext}`)
      toast({ title: 'Export downloaded', description: `${format.toUpperCase()} export` })
    } catch (err) {
      toast({
        title: 'Export failed',
        description: (err as Error).message,
        variant: 'destructive',
      })
    }
  }

  const progress = timeline.total > 0 ? time / timeline.total : 0

  return (
    <div className="w-full max-w-[380px] mx-auto space-y-3">
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={W}
          height={H}
          className="w-full rounded-xl border border-zinc-800 bg-zinc-950 cursor-pointer"
          style={{ aspectRatio: `${W}/${H}` }}
          onClick={() => (playing ? pause() : play())}
          aria-label="Video preview"
        />
        {exporting && (
          <div className="absolute inset-0 rounded-xl bg-black/70 flex flex-col items-center justify-center gap-3 text-center px-6">
            <Loader2 className="h-8 w-8 animate-spin text-amber-400" />
            <p className="text-sm font-semibold text-zinc-100">Rendering WebM…</p>
            <p className="text-xs text-zinc-400">
              {(progress * 100).toFixed(0)}% — real-time capture, keep this tab visible
            </p>
          </div>
        )}
        {!exporting && !assetsReady && loadProgress.total > 0 && (
          <div className="absolute inset-0 rounded-xl bg-black/60 flex flex-col items-center justify-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-amber-400" />
            <p className="text-xs text-zinc-300">
              Loading assets {loadProgress.done}/{loadProgress.total}
            </p>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="icon"
          onClick={() => (playing ? pause() : play())}
          disabled={timeline.total <= 0 || !assetsReady}
          aria-label={playing ? 'Pause' : 'Play'}
          className="bg-zinc-800 hover:bg-zinc-700"
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
        <Button
          variant="secondary"
          size="icon"
          onClick={restart}
          disabled={timeline.total <= 0 || !assetsReady}
          aria-label="Restart"
          className="bg-zinc-800 hover:bg-zinc-700"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
        <span className="text-xs font-mono text-zinc-400 tabular-nums">
          {formatClock(time)} / {formatClock(timeline.total)}
        </span>
        <Slider
          className="flex-1 mx-1"
          value={[Math.min(time, timeline.total)]}
          min={0}
          max={Math.max(timeline.total, 0.1)}
          step={0.05}
          onValueChange={([v]) => seek(v)}
          disabled={timeline.total <= 0 || exporting}
          aria-label="Seek"
        />
        <Button
          variant="secondary"
          size="icon"
          onClick={toggleMute}
          aria-label={muted ? 'Unmute' : 'Mute'}
          className="bg-zinc-800 hover:bg-zinc-700"
        >
          {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </Button>
      </div>

      <div className="grid grid-cols-4 gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={exportWebM}
          disabled={exportDisabled}
          className="border-zinc-800"
        >
          {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Film className="h-4 w-4" />}
          WebM
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void handleDownload('srt')}
          disabled={exportDisabled}
          className="border-zinc-800"
        >
          <Captions className="h-4 w-4" /> SRT
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void handleDownload('json')}
          disabled={exportDisabled}
          className="border-zinc-800"
        >
          <Braces className="h-4 w-4" /> JSON
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => void handleDownload('remotion')}
          disabled={exportDisabled}
          className="border-zinc-800"
        >
          <Code2 className="h-4 w-4" /> Remotion
        </Button>
      </div>
      <p className="text-[11px] text-zinc-500 text-center">
        In-browser render: Ken Burns motion, karaoke captions, synced narration. Remotion export
        renders the same timeline as a studio-grade MP4 on your machine.
      </p>
    </div>
  )
}
