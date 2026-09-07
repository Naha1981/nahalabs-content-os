// NahaLabs Content OS — Video Factory pipeline runner.
//
// MoneyPrinter-style single workflow, hardened with the content-engine's
// worker semantics: idempotent steps (safe to resume / retry), per-asset
// statuses, and a quality gate before anything is called "ready".
//
//   research -> script -> visuals -> narration -> captions -> quality_review
//
// The runner is fire-and-forget from the API layer; the UI polls the project.
// Every DB write goes through dbRetry (SQLite can momentarily lock under the
// polling reads).

import { db } from '@/lib/db'
import { getRouter } from '@/lib/providers'
import { readAssetBuffer, saveAsset } from '@/lib/assets'
import { buildSubtitleTrack, estimateDuration, rescaleTrack, tokenize } from '@/lib/subtitles'
import type {
  QualityCheck,
  QualityReport,
  ResearchBrief,
  ScriptMeta,
  SubtitleTrack,
} from '@/lib/types'

const globalForPipeline = globalThis as unknown as {
  __vfActive?: Set<string>
  __vfSceneActive?: Set<string>
}

const ACTIVE = (globalForPipeline.__vfActive ??= new Set<string>())
const SCENE_ACTIVE = (globalForPipeline.__vfSceneActive ??= new Set<string>())

export function isPipelineRunning(projectId: string): boolean {
  return ACTIVE.has(projectId)
}

async function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

async function dbRetry<T>(fn: () => Promise<T>): Promise<T> {
  let lastErr: unknown
  for (let i = 0; i < 3; i++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      await sleep(120 * (i + 1))
    }
  }
  throw lastErr
}

type ProjectRow = {
  id: string
  title: string
  topic: string
  mode: string
  productUrl: string | null
  platform: string
  style: string
  voice: string
  speed: number
  durationTarget: number
  researchJson: string | null
  scriptJson: string | null
}

type SceneRow = {
  id: string
  projectId: string
  position: number
  narration: string
  onScreenText: string | null
  visualPrompt: string | null
  imageUrl: string | null
  imageStatus: string
  audioUrl: string | null
  audioStatus: string
  audioDuration: number | null
  subtitlesJson: string | null
}

async function setProject(id: string, data: Record<string, unknown>): Promise<void> {
  await dbRetry(() => db.videoProject.update({ where: { id }, data }))
}

async function logEvent(
  projectId: string,
  step: string,
  status: 'running' | 'done' | 'warning' | 'failed' | 'skipped',
  message: string
): Promise<void> {
  try {
    await dbRetry(() =>
      db.pipelineEvent.create({ data: { projectId, step, status, message } })
    )
  } catch {
    // logging must never break the pipeline
  }
}

async function loadScenes(projectId: string): Promise<SceneRow[]> {
  return db.videoScene.findMany({ where: { projectId }, orderBy: { position: 'asc' } })
}

async function mapLimit<T>(
  items: T[],
  limit: number,
  fn: (item: T) => Promise<void>
): Promise<void> {
  let next = 0
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const idx = next++
      try {
        await fn(items[idx])
      } catch {
        // per-item errors are recorded by the fn itself
      }
    }
  })
  await Promise.all(workers)
}

function stripHtml(html: string): string {
  return html
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n))
}

const STYLE_IMAGE_HINTS: Record<string, string> = {
  educational: 'clean editorial photography, bright natural light',
  hype: 'high-energy bold photography, dynamic angles, vivid color',
  storytelling: 'cinematic photography, moody atmospheric light',
  listicle: 'modern minimal photography, crisp studio light',
  ugc: 'authentic casual phone-photo look, natural imperfect framing',
}

// ---------------------------------------------------------------------------
// Step 1 — Research
// ---------------------------------------------------------------------------

async function runResearch(project: ProjectRow): Promise<void> {
  const router = getRouter()
  await setProject(project.id, { status: 'researching', stepDetail: 'Searching the live web' })
  await logEvent(project.id, 'research', 'running', `Researching: ${project.topic}`)

  let brief: ResearchBrief | null = null
  const sources: { title: string; url: string }[] = []

  if (project.mode === 'ugc' && project.productUrl) {
    await setProject(project.id, { stepDetail: 'Reading product page' })
    try {
      const page = await router.readPage(project.productUrl)
      const pageText = stripHtml(page.html).slice(0, 6000)
      sources.push({ title: page.title || project.productUrl, url: project.productUrl })
      await logEvent(project.id, 'research', 'running', `Read product page: ${page.title}`)
      const extracted = await router.generateStructuredJson<{
        summary: string
        keyPoints: string[]
        hooks: string[]
        productName?: string
      }>([
        {
          role: 'assistant',
          content:
            'You are a UGC ad strategist. Extract product intelligence from a product page and return STRICT JSON only: {"summary": string, "keyPoints": string[], "hooks": string[], "productName": string}. keyPoints: 4-6 concrete selling points. hooks: 3 scroll-stopping opening lines a creator could say on camera.',
        },
        {
          role: 'user',
          content: `Product URL: ${project.productUrl}\nProduct notes/topic: ${project.topic}\n\nPage content:\n${pageText}`,
        },
      ])
      brief = {
        summary: extracted.summary,
        keyPoints: extracted.keyPoints ?? [],
        hooks: extracted.hooks ?? [],
        sources,
      }
    } catch (err) {
      await logEvent(
        project.id,
        'research',
        'warning',
        `Product page read failed (${(err as Error).message}) — falling back to web search`
      )
    }
  }

  if (!brief) {
    const results = await router.search(project.topic, 6)
    for (const r of results.slice(0, 6)) {
      sources.push({ title: r.name, url: r.url })
    }
    await logEvent(
      project.id,
      'research',
      'running',
      `Found ${results.length} web sources — distilling a research brief`
    )
    const resultsText = results
      .slice(0, 6)
      .map((r, i) => `${i + 1}. ${r.name} (${r.host_name})\n${r.snippet}`)
      .join('\n\n')
    const extracted = await router.generateStructuredJson<{
      summary: string
      keyPoints: string[]
      hooks: string[]
    }>([
      {
        role: 'assistant',
        content:
          'You are a short-form video researcher. Return STRICT JSON only: {"summary": string, "keyPoints": string[], "hooks": string[]}. summary: 2-3 sentences of usable facts. keyPoints: 4-6 specific, factual points worth mentioning in a video. hooks: 3 punchy opening lines tailored for vertical short-form video. Base everything strictly on the search results; do not invent statistics.',
      },
      {
        role: 'user',
        content: `Topic: ${project.topic}\nPlatform: ${project.platform}\nStyle: ${project.style}\n\nSearch results:\n${resultsText}`,
      },
    ])
    brief = {
      summary: extracted.summary,
      keyPoints: extracted.keyPoints ?? [],
      hooks: extracted.hooks ?? [],
      sources,
    }
  }

  await setProject(project.id, {
    researchJson: JSON.stringify(brief),
    stepDetail: 'Research brief ready',
  })
  await logEvent(project.id, 'research', 'done', `Research brief ready (${brief.sources.length} sources)`)
}

// ---------------------------------------------------------------------------
// Step 2 — Script
// ---------------------------------------------------------------------------

async function runScript(project: ProjectRow): Promise<void> {
  const router = getRouter()
  await setProject(project.id, { status: 'scripting', stepDetail: 'Writing the script' })
  await logEvent(project.id, 'script', 'running', 'Generating scene-by-scene script')

  const research: ResearchBrief = project.researchJson
    ? JSON.parse(project.researchJson)
    : { summary: '', keyPoints: [], hooks: [], sources: [] }

  const sceneCount = clamp(Math.round(project.durationTarget / 6), 3, 8)

  const isUgc = project.mode === 'ugc'
  const systemPrompt = isUgc
    ? 'You are a UGC ad scriptwriter. You write authentic, creator-style vertical video ads: conversational, first-person, like a real person talking to camera. No ad-speak, no corporate voice.'
    : 'You are a short-form vertical video scriptwriter. You write punchy, retention-optimized scripts for TikTok/Reels/Shorts: strong hook in the first 2 seconds, tight pacing, clear payoff.'

  const userPrompt = `Topic: ${project.topic}
Platform: ${project.platform} (vertical video, fast cuts)
Style: ${project.style}
Target total duration: ~${project.durationTarget} seconds
Number of scenes: EXACTLY ${sceneCount}

Research brief:
${JSON.stringify(research).slice(0, 4000)}

Rules:
- Each scene's "narration" is what the voice says: 12-25 words, plain spoken sentences, no stage directions, no emojis.
- Each scene's "onScreenText" is a big bold overlay: max 6 words, uppercase-friendly, punchy.
- Each scene's "visualPrompt" describes ONE still image for AI image generation: concrete visual subject, setting, composition (vertical 9:16), lighting, style. Never ask for text or logos inside the image.
- ${isUgc ? 'Scene 1 opens like a creator mid-thought ("Okay so I have to show you this..."). Last scene is a soft CTA.' : 'Scene 1 is the hook. Last scene delivers the payoff/CTA.'}

Return STRICT JSON only:
{"title": string, "hook": string, "cta": string, "hashtags": string[], "scenes": [{"narration": string, "onScreenText": string, "visualPrompt": string}]}`

  const data = await router.generateStructuredJson<{
    title?: string
    hook?: string
    cta?: string
    hashtags?: string[]
    scenes?: { narration?: string; onScreenText?: string; visualPrompt?: string }[]
  }>([
    { role: 'assistant', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ])

  const rawScenes = (data.scenes ?? []).filter((s) => (s.narration ?? '').trim().length > 0)
  if (rawScenes.length === 0) {
    throw new Error('Script generation returned no usable scenes')
  }

  const script: ScriptMeta = {
    title: (data.title ?? project.topic).slice(0, 120),
    hook: data.hook ?? '',
    cta: data.cta ?? '',
    hashtags: (data.hashtags ?? []).slice(0, 8).map((h) =>
      h.startsWith('#') ? h.slice(0, 40) : `#${h.replace(/\s+/g, '')}`.slice(0, 40)
    ),
  }

  await dbRetry(() =>
    db.videoScene.createMany({
      data: rawScenes.map((s, i) => ({
        projectId: project.id,
        position: i + 1,
        narration: (s.narration ?? '').trim().slice(0, 950),
        onScreenText: (s.onScreenText ?? '').trim().slice(0, 80) || null,
        visualPrompt: (s.visualPrompt ?? '').trim().slice(0, 600) || null,
      })),
    })
  )

  await setProject(project.id, {
    scriptJson: JSON.stringify(script),
    title: script.title,
    stepDetail: 'Script ready',
  })
  await logEvent(
    project.id,
    'script',
    'done',
    `Script ready: ${rawScenes.length} scenes, title "${script.title}"`
  )
}

// ---------------------------------------------------------------------------
// Step 3 — Visuals
// ---------------------------------------------------------------------------

async function runVisuals(project: ProjectRow): Promise<void> {
  const router = getRouter()
  const scenes = await loadScenes(project.id)
  const todo = scenes.filter((s) => s.imageStatus !== 'ready')
  if (todo.length === 0) {
    await logEvent(project.id, 'visuals', 'skipped', 'All visuals already generated')
    return
  }
  await setProject(project.id, {
    status: 'visualizing',
    stepDetail: `Generating ${todo.length} scene visuals`,
  })
  await logEvent(project.id, 'visuals', 'running', `Generating ${todo.length} images (2 in parallel)`)

  const styleHint = STYLE_IMAGE_HINTS[project.style] ?? STYLE_IMAGE_HINTS.educational
  let done = 0

  await mapLimit(todo, 2, async (scene) => {
    await dbRetry(() =>
      db.videoScene.update({ where: { id: scene.id }, data: { imageStatus: 'generating' } })
    )
    try {
      const prompt = [
        scene.visualPrompt ?? scene.narration.slice(0, 200),
        'vertical 9:16 composition',
        styleHint,
        'high quality, detailed, no text, no watermark',
      ]
        .filter(Boolean)
        .join(', ')
      const { base64 } = await router.generateImage(prompt, '768x1344')
      const url = await saveAsset(
        project.id,
        `scene-${scene.position}-${Date.now()}.png`,
        Buffer.from(base64, 'base64')
      )
      await dbRetry(() =>
        db.videoScene.update({
          where: { id: scene.id },
          data: { imageUrl: url, imageStatus: 'ready', imageQualityJson: null },
        })
      )
      done++
      await setProject(project.id, { stepDetail: `Visuals: ${done}/${todo.length} done` })
    } catch (err) {
      await dbRetry(() =>
        db.videoScene.update({ where: { id: scene.id }, data: { imageStatus: 'failed' } })
      )
      await logEvent(
        project.id,
        'visuals',
        'warning',
        `Scene ${scene.position} image failed: ${(err as Error).message}`
      )
    }
  })

  const failed = todo.length - done
  await logEvent(
    project.id,
    'visuals',
    failed > 0 ? 'warning' : 'done',
    failed > 0 ? `${done}/${todo.length} images generated, ${failed} failed` : `All ${done} images generated`
  )
}

// ---------------------------------------------------------------------------
// Step 4 — Narration
// ---------------------------------------------------------------------------

function cleanNarrationForTts(text: string): string {
  return text
    .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
}

async function runNarration(project: ProjectRow): Promise<void> {
  const router = getRouter()
  const scenes = await loadScenes(project.id)
  const todo = scenes.filter((s) => s.audioStatus !== 'ready')
  if (todo.length === 0) {
    await logEvent(project.id, 'narration', 'skipped', 'All narration already generated')
    return
  }
  await setProject(project.id, {
    status: 'narrating',
    stepDetail: `Synthesizing ${todo.length} voice tracks`,
  })
  await logEvent(project.id, 'narration', 'running', `TTS: ${todo.length} scenes, voice ${project.voice}`)

  let done = 0
  // Sequential on purpose: the TTS API rate-limits bursts (429) hard.
  await mapLimit(todo, 1, async (scene) => {
    await dbRetry(() =>
      db.videoScene.update({ where: { id: scene.id }, data: { audioStatus: 'generating' } })
    )
    try {
      const text = cleanNarrationForTts(scene.narration).slice(0, 1000)
      const buffer = await router.synthesizeSpeech({
        text,
        voice: project.voice,
        speed: project.speed,
      })
      const url = await saveAsset(
        project.id,
        `scene-${scene.position}-${Date.now()}.wav`,
        buffer
      )
      const est = estimateDuration(text)
      await dbRetry(() =>
        db.videoScene.update({
          where: { id: scene.id },
          data: {
            audioUrl: url,
            audioStatus: 'ready',
            audioDuration: scene.audioDuration ?? est,
            subtitlesJson: JSON.stringify(buildSubtitleTrack(text, est, 'estimated')),
          },
        })
      )
      done++
      await setProject(project.id, { stepDetail: `Narration: ${done}/${todo.length} done` })
      await sleep(400) // spacing keeps the TTS API happy
    } catch (err) {
      await dbRetry(() =>
        db.videoScene.update({ where: { id: scene.id }, data: { audioStatus: 'failed' } })
      )
      await logEvent(
        project.id,
        'narration',
        'warning',
        `Scene ${scene.position} TTS failed: ${(err as Error).message}`
      )
    }
  })

  const failed = todo.length - done
  await logEvent(
    project.id,
    'narration',
    failed > 0 ? 'warning' : 'done',
    failed > 0 ? `${done}/${todo.length} voice tracks done, ${failed} failed` : `All ${done} voice tracks generated`
  )
}

// ---------------------------------------------------------------------------
// Step 5 — Captions
// ---------------------------------------------------------------------------

async function recomputeSubtitlesForScene(scene: SceneRow): Promise<void> {
  const narration = cleanNarrationForTts(scene.narration)
  const existing: SubtitleTrack | null = scene.subtitlesJson
    ? JSON.parse(scene.subtitlesJson)
    : null
  const track =
    existing && scene.audioDuration != null
      ? rescaleTrack(existing, scene.audioDuration)
      : buildSubtitleTrack(narration, scene.audioDuration, scene.audioDuration != null ? 'probed' : 'estimated')
  await dbRetry(() =>
    db.videoScene.update({ where: { id: scene.id }, data: { subtitlesJson: JSON.stringify(track) } })
  )
}

async function runSubtitles(project: ProjectRow): Promise<void> {
  await setProject(project.id, { status: 'subtitling', stepDetail: 'Timing word-level captions' })
  const scenes = await loadScenes(project.id)
  let n = 0
  for (const scene of scenes) {
    if (!scene.audioUrl) continue
    await recomputeSubtitlesForScene(scene)
    n++
  }
  await logEvent(
    project.id,
    'captions',
    'done',
    `${n} caption tracks timed (word-level; refined against audio duration when probed)`
  )
}

// ---------------------------------------------------------------------------
// Step 6 — Quality gate (mirrors app/services/quality_engine.py)
// ---------------------------------------------------------------------------

function wordOverlap(a: string, b: string): number {
  const wa = tokenize(a.toLowerCase())
  const wb = tokenize(b.toLowerCase())
  if (wb.length === 0) return 0
  const pool = [...wa]
  let hits = 0
  for (const w of wb) {
    const idx = pool.indexOf(w)
    if (idx >= 0) {
      hits++
      pool.splice(idx, 1)
    }
  }
  return hits / wb.length
}

async function imageToDataUrl(publicUrl: string): Promise<string> {
  const sharp = (await import('sharp')).default
  const buf = await readAssetBuffer(publicUrl)
  const small = await sharp(buf).resize({ width: 360 }).jpeg({ quality: 70 }).toBuffer()
  return `data:image/jpeg;base64,${small.toString('base64')}`
}

async function runQuality(project: ProjectRow): Promise<void> {
  const router = getRouter()
  await setProject(project.id, { status: 'quality_review', stepDetail: 'Running quality checks' })
  await logEvent(project.id, 'quality', 'running', 'Quality gate: technical checks')

  const scenes = await loadScenes(project.id)
  const checks: QualityCheck[] = []

  const imagesReady = scenes.filter((s) => s.imageStatus === 'ready')
  const audioReady = scenes.filter((s) => s.audioStatus === 'ready')

  checks.push({
    id: 'images',
    label: `Scene visuals present (${imagesReady.length}/${scenes.length})`,
    status: imagesReady.length === scenes.length ? 'pass' : imagesReady.length > 0 ? 'warn' : 'fail',
    detail: imagesReady.length < scenes.length ? 'Some scene images failed to generate — retry from the storyboard' : undefined,
  })
  checks.push({
    id: 'audio',
    label: `Narration tracks present (${audioReady.length}/${scenes.length})`,
    status: audioReady.length === scenes.length ? 'pass' : audioReady.length > 0 ? 'warn' : 'fail',
    detail: audioReady.length < scenes.length ? 'Some voice tracks failed — retry from the storyboard' : undefined,
  })
  checks.push({
    id: 'scenes',
    label: `Scene count (${scenes.length})`,
    status: scenes.length >= 3 ? 'pass' : 'warn',
    detail: scenes.length < 3 ? 'Very few scenes for a vertical video' : undefined,
  })

  const estTotal = scenes.reduce((acc, s) => acc + (s.audioDuration ?? estimateDuration(s.narration)), 0)
  const pacingDev = Math.abs(estTotal - project.durationTarget) / project.durationTarget
  checks.push({
    id: 'pacing',
    label: `Pacing vs target (${estTotal.toFixed(0)}s / ${project.durationTarget}s)`,
    status: pacingDev <= 0.3 ? 'pass' : 'warn',
    detail: pacingDev > 0.3 ? 'Estimated runtime drifts from the target duration' : undefined,
  })

  // Visual QC — one multi-image VLM call, downscaled frames
  let visualScore: number | null = null
  if (imagesReady.length > 0) {
    try {
      await setProject(project.id, { stepDetail: 'Quality gate: vision review of frames' })
      const inputs = await Promise.all(
        imagesReady.map(async (s) => ({
          scene: s,
          dataUrl: await imageToDataUrl(s.imageUrl as string),
        }))
      )
      const instruction = `You are reviewing AI-generated video frames. For each image, judge how well it matches its intended visual description. Reply STRICT JSON only: {"results":[{"index":1,"score":7,"issue":"..."}]} where index is 1-based image order, score is 1-10 (10 = matches perfectly, usable in a published video), issue is a short note or empty string.
Descriptions:
${inputs.map((inp, i) => `${i + 1}. ${inp.scene.visualPrompt ?? inp.scene.narration.slice(0, 120)}`).join('\n')}`
      const raw = await router.analyzeImages(
        inputs.map((i) => ({ dataUrl: i.dataUrl, prompt: i.scene.visualPrompt ?? '' })),
        instruction
      )
      let parsed: { results?: { index?: number; score?: number; issue?: string }[] }
      try {
        const text = raw.trim()
        const start = text.indexOf('{')
        const end = text.lastIndexOf('}')
        parsed = JSON.parse(start >= 0 && end > start ? text.slice(start, end + 1) : text)
      } catch {
        parsed = {}
      }
      const results = parsed.results ?? []
      const scored = results.filter((r) => typeof r.score === 'number')
      if (scored.length > 0) {
        visualScore = scored.reduce((a, r) => a + (r.score as number), 0) / scored.length / 10
        for (const r of scored) {
          const scene = imagesReady[(r.index ?? 0) - 1]
          if (scene && r.score != null) {
            await dbRetry(() =>
              db.videoScene.update({
                where: { id: scene.id },
                data: {
                  imageQualityJson: JSON.stringify({
                    score: r.score,
                    issue: (r.issue ?? '').slice(0, 200) || undefined,
                  }),
                },
              })
            )
          }
        }
        const avg10 = visualScore * 10
        checks.push({
          id: 'visual_match',
          label: `Vision review of frames (avg ${avg10.toFixed(1)}/10)`,
          status: avg10 >= 6 ? 'pass' : 'warn',
          detail: avg10 < 6 ? 'Some frames scored low against their visual prompts' : undefined,
        })
      }
    } catch (err) {
      checks.push({
        id: 'visual_match',
        label: 'Vision review of frames',
        status: 'skipped',
        detail: `Vision QC unavailable: ${(err as Error).message}`,
      })
    }
  }

  // Narration QC — ASR the first audio scene and compare to the script
  let narrationScore: number | null = null
  let transcriptCheck: QualityReport['transcriptCheck']
  const audioScene = scenes.find((s) => s.audioStatus === 'ready' && s.audioUrl)
  if (audioScene) {
    try {
      await setProject(project.id, { stepDetail: 'Quality gate: transcription check' })
      const buf = await readAssetBuffer(audioScene.audioUrl as string)
      const transcript = await router.transcribeAudio(buf)
      const similarity = wordOverlap(transcript, audioScene.narration)
      narrationScore = similarity
      transcriptCheck = { similarity, transcript }
      checks.push({
        id: 'narration_match',
        label: `Speech-to-script match (scene 1: ${(similarity * 100).toFixed(0)}%)`,
        status: similarity >= 0.7 ? 'pass' : 'warn',
        detail: similarity < 0.7 ? 'Transcription differs noticeably from the script' : undefined,
      })
    } catch (err) {
      checks.push({
        id: 'narration_match',
        label: 'Speech-to-script match',
        status: 'skipped',
        detail: `ASR QC unavailable: ${(err as Error).message}`,
      })
    }
  }

  const hardFail = checks.some((c) => c.status === 'fail')
  const scoredChecks = checks.filter((c) => c.status === 'pass').length
  const totalChecks = checks.filter((c) => c.status !== 'skipped').length
  const technical = totalChecks === 0 ? 1 : scoredChecks / totalChecks

  const parts: number[] = [technical]
  if (visualScore != null) parts.push(visualScore)
  if (narrationScore != null) parts.push(narrationScore)
  const overall = parts.reduce((a, b) => a + b, 0) / parts.length

  const report: QualityReport = {
    checks,
    scores: { technical, visual: visualScore, narration: narrationScore, overall },
    passed: !hardFail && overall >= 0.7,
    transcriptCheck,
    ranAt: new Date().toISOString(),
  }

  await setProject(project.id, {
    qualityJson: JSON.stringify(report),
    status: report.passed ? 'approved_ready' : 'quality_failed',
    stepDetail: report.passed ? 'Quality gate passed' : 'Quality gate flagged issues',
    error: null,
  })
  await logEvent(
    project.id,
    'quality',
    report.passed ? 'done' : 'warning',
    report.passed
      ? `Quality gate passed (overall ${(overall * 100).toFixed(0)}%)`
      : `Quality gate flagged issues (overall ${(overall * 100).toFixed(0)}%) — assets still playable`
  )
}

// ---------------------------------------------------------------------------
// Orchestration
// ---------------------------------------------------------------------------

async function runPipelineInternal(projectId: string): Promise<void> {
  const project = await db.videoProject.findUnique({ where: { id: projectId } })
  if (!project) return

  // 1 — Research (cached once present)
  if (!project.researchJson) {
    await runResearch(project)
  } else {
    await logEvent(projectId, 'research', 'skipped', 'Research brief already cached')
  }

  // 2 — Script
  let scenes = await loadScenes(projectId)
  if (scenes.length === 0) {
    await runScript(project)
    scenes = await loadScenes(projectId)
  } else {
    await logEvent(projectId, 'script', 'skipped', 'Script already generated')
  }

  // 3-5 — Assets (idempotent: only missing/failed items regenerate)
  await runVisuals(project)
  await runNarration(project)
  await runSubtitles(project)

  // 6 — Quality gate
  await runQuality(project)

  await logEvent(projectId, 'pipeline', 'done', 'Pipeline finished')
}

export function runPipeline(projectId: string): void {
  if (ACTIVE.has(projectId)) return
  ACTIVE.add(projectId)
  void (async () => {
    try {
      await runPipelineInternal(projectId)
    } catch (err) {
      const message = (err as Error).message ?? 'Unknown pipeline error'
      await setProject(projectId, { status: 'failed', error: message, stepDetail: null })
      await logEvent(projectId, 'pipeline', 'failed', message)
    } finally {
      ACTIVE.delete(projectId)
    }
  })()
}

// ---------------------------------------------------------------------------
// Per-scene regeneration (storyboard retry buttons)
// ---------------------------------------------------------------------------

export function regenerateScene(sceneId: string, target: 'image' | 'audio'): void {
  if (SCENE_ACTIVE.has(sceneId)) return
  SCENE_ACTIVE.add(sceneId)
  void (async () => {
    try {
      const scene = await db.videoScene.findUnique({ where: { id: sceneId } })
      const project = scene
        ? await db.videoProject.findUnique({ where: { id: scene.projectId } })
        : null
      if (!scene || !project) return
      const router = getRouter()

      if (target === 'image') {
        await dbRetry(() =>
          db.videoScene.update({
            where: { id: scene.id },
            data: { imageStatus: 'generating', imageQualityJson: null },
          })
        )
        try {
          const styleHint = STYLE_IMAGE_HINTS[project.style] ?? STYLE_IMAGE_HINTS.educational
          const prompt = [
            scene.visualPrompt ?? scene.narration.slice(0, 200),
            'vertical 9:16 composition',
            styleHint,
            'high quality, detailed, no text, no watermark',
          ]
            .filter(Boolean)
            .join(', ')
          const { base64 } = await router.generateImage(prompt, '768x1344')
          const url = await saveAsset(
            project.id,
            `scene-${scene.position}-${Date.now()}.png`,
            Buffer.from(base64, 'base64')
          )
          await dbRetry(() =>
            db.videoScene.update({
              where: { id: scene.id },
              data: { imageUrl: url, imageStatus: 'ready' },
            })
          )
          await logEvent(project.id, 'visuals', 'done', `Scene ${scene.position} visual regenerated`)
        } catch (err) {
          await dbRetry(() =>
            db.videoScene.update({ where: { id: scene.id }, data: { imageStatus: 'failed' } })
          )
          await logEvent(
            project.id,
            'visuals',
            'failed',
            `Scene ${scene.position} image regen failed: ${(err as Error).message}`
          )
        }
      } else {
        await dbRetry(() =>
          db.videoScene.update({
            where: { id: scene.id },
            data: { audioStatus: 'generating' },
          })
        )
        try {
          const text = cleanNarrationForTts(scene.narration).slice(0, 1000)
          const buffer = await router.synthesizeSpeech({
            text,
            voice: project.voice,
            speed: project.speed,
          })
          const url = await saveAsset(
            project.id,
            `scene-${scene.position}-${Date.now()}.wav`,
            buffer
          )
          const est = estimateDuration(text)
          await dbRetry(() =>
            db.videoScene.update({
              where: { id: scene.id },
              data: {
                audioUrl: url,
                audioStatus: 'ready',
                audioDuration: est,
                subtitlesJson: JSON.stringify(buildSubtitleTrack(text, est, 'estimated')),
              },
            })
          )
          await logEvent(project.id, 'narration', 'done', `Scene ${scene.position} narration regenerated`)
        } catch (err) {
          await dbRetry(() =>
            db.videoScene.update({ where: { id: scene.id }, data: { audioStatus: 'failed' } })
          )
          await logEvent(
            project.id,
            'narration',
            'failed',
            `Scene ${scene.position} TTS regen failed: ${(err as Error).message}`
          )
        }
      }
    } finally {
      SCENE_ACTIVE.delete(sceneId)
    }
  })()
}

export { buildSubtitleTrack, rescaleTrack }
