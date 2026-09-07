'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ArrowRight,
  AudioLines,
  Clapperboard,
  ImageIcon,
  PenLine,
  Plus,
  Search,
  ShieldCheck,
  Type,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import {
  ACTIVE_STATUSES,
  PIPELINE_STEPS,
  type Project,
  type ProjectSummary,
  type Scene,
} from '@/lib/types'
import { CreateForm, type CreatePayload } from './create-form'
import { ProjectCard, ProjectCardPlaceholder } from './project-card'
import { ProjectView, } from './project-view'
import type { ScenePatch } from './scene-card'

const STEP_ICONS = [Search, PenLine, ImageIcon, AudioLines, Type, ShieldCheck]

export function FactoryApp() {
  const [view, setView] = useState<'home' | 'project'>('home')
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null)
  const [project, setProject] = useState<Project | null>(null)
  const [creating, setCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [runBusy, setRunBusy] = useState(false)
  const [sceneSaving, setSceneSaving] = useState(false)
  const { toast } = useToast()

  const projectRef = useRef<Project | null>(null)
  useEffect(() => {
    projectRef.current = project
  }, [project])

  const watchTimers = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map())

  const loadProjects = useCallback(async () => {
    try {
      const res = await fetch('/api/projects')
      if (!res.ok) return
      const data = (await res.json()) as { projects: ProjectSummary[] }
      setProjects(data.projects)
    } catch {
      /* transient */
    }
  }, [])

  useEffect(() => {
    void loadProjects()
  }, [loadProjects, view])

  // Refresh the home grid while anything is actively generating
  const anyActive = projects?.some((p) => ACTIVE_STATUSES.includes(p.status)) ?? false
  useEffect(() => {
    if (view !== 'home' || !anyActive) return
    const t = setInterval(() => void loadProjects(), 3000)
    return () => clearInterval(t)
  }, [view, anyActive, loadProjects])

  // Poll the open project while the pipeline runs
  const projectId = project?.id
  const projectStatus = project?.status
  useEffect(() => {
    if (!projectId || !projectStatus) return
    if (!ACTIVE_STATUSES.includes(projectStatus)) return
    const t = setInterval(async () => {
      try {
        const res = await fetch(`/api/projects/${projectId}`)
        if (!res.ok) return
        const data = (await res.json()) as { project: Project }
        setProject((cur) => (cur && cur.id === projectId ? data.project : cur))
      } catch {
        /* transient */
      }
    }, 1600)
    return () => clearInterval(t)
  }, [projectId, projectStatus])

  useEffect(() => {
    const timers = watchTimers.current
    return () => {
      for (const [, t] of timers) clearInterval(t)
    }
  }, [])

  function watchProjectUntilSettled(id: string) {
    if (watchTimers.current.has(id)) return
    let tries = 0
    const t = setInterval(async () => {
      tries++
      try {
        const res = await fetch(`/api/projects/${id}`)
        if (res.ok) {
          const data = (await res.json()) as { project: Project }
          setProject((cur) => (cur && cur.id === id ? data.project : cur))
          const busy = data.project.scenes.some(
            (s) => s.imageStatus === 'generating' || s.audioStatus === 'generating'
          )
          if (!busy || tries > 90) {
            clearInterval(t)
            watchTimers.current.delete(id)
            void loadProjects()
          }
        }
      } catch {
        /* keep trying */
      }
      if (tries > 90) {
        clearInterval(t)
        watchTimers.current.delete(id)
      }
    }, 2000)
    watchTimers.current.set(id, t)
  }

  const fetchProject = useCallback(async (id: string): Promise<Project | null> => {
    try {
      const res = await fetch(`/api/projects/${id}`)
      if (!res.ok) return null
      const data = (await res.json()) as { project: Project }
      return data.project
    } catch {
      return null
    }
  }, [])

  const createProject = useCallback(
    async (payload: CreatePayload) => {
      setCreating(true)
      try {
        const res = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(payload),
        })
        const data = (await res.json()) as { project?: Project; error?: string }
        if (!res.ok || !data.project) {
          toast({
            title: 'Could not start the pipeline',
            description: data.error ?? 'Something went wrong',
            variant: 'destructive',
          })
          return
        }
        setProject(data.project)
        setView('project')
        toast({
          title: 'Pipeline started',
          description: 'Research → script → visuals → narration → captions → quality gate',
        })
      } catch (err) {
        toast({
          title: 'Could not start the pipeline',
          description: (err as Error).message,
          variant: 'destructive',
        })
      } finally {
        setCreating(false)
      }
    },
    [toast]
  )

  const openProject = useCallback(
    async (id: string) => {
      const p = await fetchProject(id)
      if (p) {
        setProject(p)
        setView('project')
      }
    },
    [fetchProject]
  )

  const deleteProject = useCallback(
    async (id: string) => {
      setDeletingId(id)
      try {
        const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' })
        if (!res.ok) throw new Error(`Delete failed (${res.status})`)
        if (projectRef.current?.id === id) {
          setProject(null)
          setView('home')
        }
        toast({ title: 'Project deleted' })
        await loadProjects()
      } catch (err) {
        toast({
          title: 'Delete failed',
          description: (err as Error).message,
          variant: 'destructive',
        })
      } finally {
        setDeletingId(null)
      }
    },
    [loadProjects, toast]
  )

  const runProject = useCallback(
    async (id: string) => {
      setRunBusy(true)
      try {
        await fetch(`/api/projects/${id}/run`, { method: 'POST' })
        const p = await fetchProject(id)
        if (p) setProject(p)
        toast({ title: 'Pipeline resumed', description: 'Completed steps skip, failed assets retry' })
      } finally {
        setRunBusy(false)
      }
    },
    [fetchProject, toast]
  )

  const regenerateScene = useCallback(
    async (sceneId: string, target: 'image' | 'audio') => {
      try {
        const res = await fetch(`/api/scenes/${sceneId}/regenerate`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ target }),
        })
        if (!res.ok) {
          const data = (await res.json().catch(() => ({}))) as { error?: string }
          toast({
            title: 'Could not regenerate',
            description: data.error ?? 'Something went wrong',
            variant: 'destructive',
          })
          return
        }
        setProject((cur) =>
          cur
            ? {
                ...cur,
                scenes: cur.scenes.map((s) =>
                  s.id === sceneId
                    ? {
                        ...s,
                        [target === 'image' ? 'imageStatus' : 'audioStatus']: 'generating',
                      }
                    : s
                ),
              }
            : cur
        )
        const current = projectRef.current
        if (current) watchProjectUntilSettled(current.id)
      } catch (err) {
        toast({
          title: 'Could not regenerate',
          description: (err as Error).message,
          variant: 'destructive',
        })
      }
    },
    [toast]
  )

  const patchScene = useCallback(
    async (sceneId: string, patch: ScenePatch): Promise<Scene | null> => {
      setSceneSaving(true)
      try {
        const res = await fetch(`/api/scenes/${sceneId}`, {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(patch),
        })
        if (!res.ok) return null
        const data = (await res.json()) as { scene: Scene }
        setProject((cur) =>
          cur
            ? { ...cur, scenes: cur.scenes.map((s) => (s.id === sceneId ? data.scene : s)) }
            : cur
        )
        return data.scene
      } catch {
        return null
      } finally {
        setSceneSaving(false)
      }
    },
    []
  )

  function goHome() {
    setView('home')
    void loadProjects()
  }

  return (
    <div className="dark min-h-screen flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/85 backdrop-blur">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">
          <button
            className="flex items-center gap-2.5"
            onClick={goHome}
            aria-label="NahaLabs Video Factory home"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 text-zinc-950">
              <Clapperboard className="h-4.5 w-4.5" />
            </span>
            <span className="font-bold tracking-tight text-[15px]">NahaLabs</span>
            <span className="text-zinc-500 text-sm hidden sm:inline">Video Factory</span>
          </button>
          <span className="hidden md:inline-flex rounded-full border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-400">
            Content OS · v2.0
          </span>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-zinc-400"
              onClick={() => {
                const el = document.getElementById('projects')
                if (el) el.scrollIntoView({ behavior: 'smooth' })
                else goHome()
              }}
            >
              Library
            </Button>
            <Button
              size="sm"
              className="font-semibold"
              onClick={() => {
                setView('home')
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
            >
              <Plus className="h-4 w-4" /> New video
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
        {view === 'home' ? (
          <div className="max-w-3xl mx-auto">
            <section className="text-center mb-8 sm:mb-10">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-900 px-3 py-1 text-xs text-zinc-300">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                Open-source pipeline · research to rendered video
              </span>
              <h1 className="mt-4 text-4xl sm:text-5xl font-bold tracking-tight">
                Topic in. <span className="text-amber-400">Video out.</span>
              </h1>
              <p className="mt-3 text-zinc-400 max-w-2xl mx-auto text-sm sm:text-base">
                One workflow: live web research, an AI script with scene breakdown, generated
                vertical visuals, voiceover narration, word-level karaoke captions — then a
                quality gate before anything ships.
              </p>
              <div className="mt-6 hidden sm:flex items-center justify-center gap-1.5 flex-wrap">
                {PIPELINE_STEPS.map((step, i) => {
                  const Icon = STEP_ICONS[i]
                  return (
                    <span key={step.id} className="flex items-center gap-1.5">
                      <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-800 bg-zinc-900/70 px-2.5 py-1 text-[11px] text-zinc-300">
                        <Icon className="h-3 w-3 text-amber-400/80" />
                        {step.label}
                      </span>
                      {i < PIPELINE_STEPS.length - 1 && (
                        <ArrowRight className="h-3 w-3 text-zinc-600" />
                      )}
                    </span>
                  )
                })}
              </div>
            </section>

            <CreateForm creating={creating} onCreate={(p) => void createProject(p)} />

            <section id="projects" className="mt-10 scroll-mt-20">
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-sm font-semibold text-zinc-200">Your videos</h2>
                <span className="text-xs text-zinc-500">
                  {projects ? `${projects.length} project${projects.length === 1 ? '' : 's'}` : ''}
                </span>
              </div>
              {projects === null ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <ProjectCardPlaceholder />
                  <ProjectCardPlaceholder />
                  <ProjectCardPlaceholder />
                </div>
              ) : projects.length === 0 ? (
                <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center">
                  <Clapperboard className="h-8 w-8 text-zinc-700 mx-auto mb-3" />
                  <p className="text-sm text-zinc-400">No videos yet.</p>
                  <p className="text-xs text-zinc-500 mt-1">
                    Throw a topic in above and watch the factory run.
                  </p>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {projects.map((p) => (
                    <ProjectCard
                      key={p.id}
                      project={p}
                      onOpen={(id) => void openProject(id)}
                      onDelete={(id) => void deleteProject(id)}
                      deleting={deletingId === p.id}
                    />
                  ))}
                </div>
              )}
            </section>
          </div>
        ) : project ? (
          <ProjectView
            project={project}
            onBack={goHome}
            onRun={(id) => void runProject(id)}
            onRegenerateScene={(id, target) => void regenerateScene(id, target)}
            onPatchScene={patchScene}
            runBusy={runBusy}
            sceneSaving={sceneSaving}
          />
        ) : (
          <div className="text-center py-24 text-zinc-500">Loading project…</div>
        )}
      </main>

      <footer className="mt-auto border-t border-zinc-800 bg-zinc-950">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-5 flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-center sm:text-left">
          <p className="text-xs text-zinc-500">
            NahaLabs Content OS — Video Factory. Open pipeline: research → script → visuals →
            narration → captions → quality gate.
          </p>
          <p className="text-xs text-zinc-600 sm:ml-auto">
            Provider router ships adapters for ComfyUI / Wan / HunyuanVideo on your own GPU box ·
            Remotion export for studio-grade renders
          </p>
        </div>
      </footer>
    </div>
  )
}
