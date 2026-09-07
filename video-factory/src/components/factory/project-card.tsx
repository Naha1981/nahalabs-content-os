'use client'

import { formatDistanceToNow } from 'date-fns'
import { Clapperboard, MoreHorizontal, Trash2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { StatusBadge } from './status-badge'
import { type ProjectSummary } from '@/lib/types'

export function ProjectCard({
  project,
  onOpen,
  onDelete,
  deleting,
}: {
  project: ProjectSummary
  onOpen: (id: string) => void
  onDelete: (id: string) => void
  deleting: boolean
}) {
  const platform = project.platform.charAt(0).toUpperCase() + project.platform.slice(1)
  return (
    <Card
      className="group border-zinc-800 bg-zinc-900/50 hover:border-amber-500/40 transition-colors cursor-pointer overflow-hidden"
      onClick={() => onOpen(project.id)}
    >
      <CardContent className="p-0">
        <div className="flex gap-0">
          <div className="relative w-28 shrink-0 bg-zinc-950 aspect-[768/1344] max-h-44 overflow-hidden">
            {project.thumbUrl ? (
              <img
                src={project.thumbUrl}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center">
                <Clapperboard className="h-6 w-6 text-zinc-700" />
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0 p-4 flex flex-col gap-2">
            <div className="flex items-start justify-between gap-2">
              <p className="font-semibold truncate">{project.title}</p>
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <button
                    aria-label="Project actions"
                    className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-zinc-200 transition"
                  >
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  align="end"
                  onClick={(e) => e.stopPropagation()}
                  className="border-zinc-800 bg-zinc-900"
                >
                  <DropdownMenuItem
                    onClick={() => onDelete(project.id)}
                    disabled={deleting}
                    className="text-red-400 focus:text-red-300"
                  >
                    <Trash2 /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            <p className="text-xs text-zinc-400 line-clamp-1">{project.topic}</p>
            <div className="flex flex-wrap items-center gap-1.5 mt-auto">
              <StatusBadge status={project.status} />
              <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-400">
                {platform}
              </span>
              <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-400">
                {project.mode === 'ugc' ? 'UGC ad' : 'Topic'}
              </span>
              {project.sceneCount > 0 && (
                <span className="text-[10px] text-zinc-500">
                  {project.imagesReady}/{project.sceneCount} frames
                </span>
              )}
              <span className="text-[10px] text-zinc-500 ml-auto">
                {formatDistanceToNow(new Date(project.createdAt), { addSuffix: true })}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function ProjectCardPlaceholder() {
  return (
    <Card className="border-zinc-800/60 bg-zinc-900/30 animate-pulse">
      <CardContent className="p-0">
        <div className="flex gap-0">
          <div className="w-28 shrink-0 bg-zinc-800/60 aspect-[768/1344] max-h-44" />
          <div className="flex-1 p-4 space-y-3">
            <div className="h-4 w-3/4 rounded bg-zinc-800/60" />
            <div className="h-3 w-1/2 rounded bg-zinc-800/40" />
            <div className="h-3 w-1/3 rounded bg-zinc-800/40 mt-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
