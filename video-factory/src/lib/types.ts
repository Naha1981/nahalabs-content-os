// NahaLabs Content OS — Video Factory
// Shared DTOs used by the API routes (server) and the studio UI (client).

export type ProjectStatus =
  | 'queued'
  | 'researching'
  | 'scripting'
  | 'visualizing'
  | 'narrating'
  | 'subtitling'
  | 'quality_review'
  | 'approved_ready'
  | 'quality_failed'
  | 'failed'

export type AssetStatus = 'pending' | 'generating' | 'ready' | 'failed'

export interface WordTiming {
  w: string
  s: number // seconds, relative to scene start
  e: number
}

export interface SubtitleTrack {
  source: 'estimated' | 'probed'
  duration: number
  words: WordTiming[]
}

export interface SceneImageQuality {
  score: number // 0..10
  issue?: string
}

export interface Scene {
  id: string
  projectId: string
  position: number
  narration: string
  onScreenText: string | null
  visualPrompt: string | null
  imageUrl: string | null
  imageStatus: AssetStatus
  imageQuality: SceneImageQuality | null
  audioUrl: string | null
  audioStatus: AssetStatus
  audioDuration: number | null
  subtitles: SubtitleTrack | null
}

export interface QualityCheck {
  id: string
  label: string
  status: 'pass' | 'warn' | 'fail' | 'skipped'
  detail?: string
}

export interface QualityReport {
  checks: QualityCheck[]
  scores: {
    technical: number
    visual: number | null
    narration: number | null
    overall: number
  }
  passed: boolean
  transcriptCheck?: {
    similarity: number
    transcript: string
  }
  ranAt: string
}

export interface ResearchBrief {
  summary: string
  keyPoints: string[]
  hooks: string[]
  sources: { title: string; url: string }[]
}

export interface ScriptMeta {
  title: string
  hook: string
  cta: string
  hashtags: string[]
}

export interface PipelineEventDTO {
  id: string
  step: string
  status: 'running' | 'done' | 'warning' | 'failed' | 'skipped'
  message: string
  createdAt: string
}

export interface Project {
  id: string
  title: string
  topic: string
  mode: 'topic' | 'ugc'
  productUrl: string | null
  platform: string
  style: string
  voice: string
  speed: number
  durationTarget: number
  status: ProjectStatus
  stepDetail: string | null
  error: string | null
  research: ResearchBrief | null
  script: ScriptMeta | null
  quality: QualityReport | null
  createdAt: string
  updatedAt: string
  scenes: Scene[]
  events: PipelineEventDTO[]
}

export interface ProjectSummary {
  id: string
  title: string
  topic: string
  mode: 'topic' | 'ugc'
  platform: string
  status: ProjectStatus
  createdAt: string
  sceneCount: number
  imagesReady: number
  audioReady: number
  thumbUrl: string | null
  qualityPassed: boolean | null
}

export const ACTIVE_STATUSES: ProjectStatus[] = [
  'queued',
  'researching',
  'scripting',
  'visualizing',
  'narrating',
  'subtitling',
  'quality_review',
]

export const PIPELINE_STEPS = [
  { id: 'research', label: 'Research', statusKey: 'researching' },
  { id: 'script', label: 'Script', statusKey: 'scripting' },
  { id: 'visuals', label: 'Visuals', statusKey: 'visualizing' },
  { id: 'narration', label: 'Narration', statusKey: 'narrating' },
  { id: 'captions', label: 'Captions', statusKey: 'subtitling' },
  { id: 'quality', label: 'Quality gate', statusKey: 'quality_review' },
] as const

export type PipelineStepId = (typeof PIPELINE_STEPS)[number]['id']

export const VOICES: { value: string; label: string }[] = [
  { value: 'tongtong', label: 'Tongtong — warm & friendly' },
  { value: 'chuichui', label: 'Chuichui — lively & playful' },
  { value: 'xiaochen', label: 'Xiaochen — calm & professional' },
  { value: 'jam', label: 'Jam — British gentleman' },
  { value: 'kazi', label: 'Kazi — clear & standard' },
  { value: 'douji', label: 'Douji — natural & flowing' },
  { value: 'luodo', label: 'Luodo — expressive' },
]

export const PLATFORMS = [
  { value: 'tiktok', label: 'TikTok' },
  { value: 'reels', label: 'Instagram Reels' },
  { value: 'shorts', label: 'YouTube Shorts' },
  { value: 'youtube', label: 'YouTube' },
]

export const STYLES = [
  { value: 'educational', label: 'Educational' },
  { value: 'hype', label: 'Hype / energy' },
  { value: 'storytelling', label: 'Storytelling' },
  { value: 'listicle', label: 'Listicle' },
  { value: 'ugc', label: 'UGC creator' },
]

export function statusLabel(status: string): string {
  switch (status) {
    case 'queued': return 'Queued'
    case 'researching': return 'Researching'
    case 'scripting': return 'Writing script'
    case 'visualizing': return 'Generating visuals'
    case 'narrating': return 'Recording narration'
    case 'subtitling': return 'Timing captions'
    case 'quality_review': return 'Quality review'
    case 'approved_ready': return 'Ready'
    case 'quality_failed': return 'Needs review'
    case 'failed': return 'Failed'
    default: return status
  }
}
