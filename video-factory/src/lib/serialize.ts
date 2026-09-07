// Server-side row -> DTO serialization for the Video Factory API.

import type {
  PipelineEventDTO,
  Project,
  ProjectSummary,
  QualityReport,
  ResearchBrief,
  Scene,
  ScriptMeta,
  SubtitleTrack,
} from '@/lib/types'
import type { PipelineEvent, VideoProject, VideoScene } from '@prisma/client'

type ProjectWithRelations = VideoProject & {
  scenes: VideoScene[]
  events: PipelineEvent[]
}

export function toSceneDTO(row: VideoScene): Scene {
  let subtitles: SubtitleTrack | null = null
  try {
    subtitles = row.subtitlesJson ? (JSON.parse(row.subtitlesJson) as SubtitleTrack) : null
  } catch {
    subtitles = null
  }
  let imageQuality: Scene['imageQuality'] = null
  try {
    imageQuality = row.imageQualityJson ? JSON.parse(row.imageQualityJson) : null
  } catch {
    imageQuality = null
  }
  return {
    id: row.id,
    projectId: row.projectId,
    position: row.position,
    narration: row.narration,
    onScreenText: row.onScreenText,
    visualPrompt: row.visualPrompt,
    imageUrl: row.imageUrl,
    imageStatus: row.imageStatus as Scene['imageStatus'],
    imageQuality,
    audioUrl: row.audioUrl,
    audioStatus: row.audioStatus as Scene['audioStatus'],
    audioDuration: row.audioDuration,
    subtitles,
  }
}

export function toProjectDTO(row: ProjectWithRelations): Project {
  let research: ResearchBrief | null = null
  let script: ScriptMeta | null = null
  let quality: QualityReport | null = null
  try {
    research = row.researchJson ? JSON.parse(row.researchJson) : null
  } catch { /* keep null */ }
  try {
    script = row.scriptJson ? JSON.parse(row.scriptJson) : null
  } catch { /* keep null */ }
  try {
    quality = row.qualityJson ? JSON.parse(row.qualityJson) : null
  } catch { /* keep null */ }

  const events: PipelineEventDTO[] = [...row.events]
    .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())
    .slice(0, 40)
    .map((e) => ({
      id: e.id,
      step: e.step,
      status: e.status as PipelineEventDTO['status'],
      message: e.message,
      createdAt: e.createdAt.toISOString(),
    }))

  return {
    id: row.id,
    title: row.title,
    topic: row.topic,
    mode: row.mode as Project['mode'],
    productUrl: row.productUrl,
    platform: row.platform,
    style: row.style,
    voice: row.voice,
    speed: row.speed,
    durationTarget: row.durationTarget,
    status: row.status as Project['status'],
    stepDetail: row.stepDetail,
    error: row.error,
    research,
    script,
    quality,
    createdAt: row.createdAt.toISOString(),
    updatedAt: row.updatedAt.toISOString(),
    scenes: [...row.scenes].sort((a, b) => a.position - b.position).map(toSceneDTO),
    events,
  }
}

export function toSummaryDTO(row: VideoProject & { scenes: VideoScene[] }): ProjectSummary {
  const readyImages = row.scenes.filter((s) => s.imageStatus === 'ready')
  let qualityPassed: boolean | null = null
  try {
    qualityPassed = row.qualityJson ? (JSON.parse(row.qualityJson) as QualityReport).passed : null
  } catch {
    qualityPassed = null
  }
  return {
    id: row.id,
    title: row.title,
    topic: row.topic,
    mode: row.mode as ProjectSummary['mode'],
    platform: row.platform,
    status: row.status as ProjectSummary['status'],
    createdAt: row.createdAt.toISOString(),
    sceneCount: row.scenes.length,
    imagesReady: readyImages.length,
    audioReady: row.scenes.filter((s) => s.audioStatus === 'ready').length,
    thumbUrl: readyImages[0]?.imageUrl ?? null,
    qualityPassed,
  }
}
