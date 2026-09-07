import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { db } from '@/lib/db'
import { runPipeline } from '@/lib/pipeline'
import { toProjectDTO, toSummaryDTO } from '@/lib/serialize'

const createSchema = z.object({
  topic: z.string().trim().min(3).max(400),
  mode: z.enum(['topic', 'ugc']).default('topic'),
  productUrl: z
    .string()
    .trim()
    .url()
    .optional()
    .or(z.literal(''))
    .transform((v) => (v ? v : undefined)),
  platform: z.enum(['tiktok', 'reels', 'shorts', 'youtube']).default('tiktok'),
  style: z
    .enum(['educational', 'hype', 'storytelling', 'listicle', 'ugc'])
    .default('educational'),
  voice: z
    .enum(['tongtong', 'chuichui', 'xiaochen', 'jam', 'kazi', 'douji', 'luodo'])
    .default('tongtong'),
  speed: z.number().min(0.5).max(2.0).default(1.0),
  durationTarget: z.number().int().min(15).max(60).default(30),
})

export async function GET() {
  try {
    const rows = await db.videoProject.findMany({
      include: { scenes: true },
      orderBy: { createdAt: 'desc' },
      take: 60,
    })
    return NextResponse.json({ projects: rows.map(toSummaryDTO) })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to list projects' },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const parsed = createSchema.safeParse(body)
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid request', issues: parsed.error.issues.map((i) => i.message) },
        { status: 400 }
      )
    }
    const input = parsed.data
    if (input.mode === 'ugc' && !input.productUrl) {
      return NextResponse.json(
        { error: 'UGC ad mode requires a product URL' },
        { status: 400 }
      )
    }

    const project = await db.videoProject.create({
      data: {
        title: input.topic.slice(0, 90),
        topic: input.topic,
        mode: input.mode,
        productUrl: input.productUrl ?? null,
        platform: input.platform,
        style: input.mode === 'ugc' ? 'ugc' : input.style,
        voice: input.voice,
        speed: input.speed,
        durationTarget: input.durationTarget,
        status: 'queued',
      },
      include: { scenes: true, events: true },
    })

    await db.pipelineEvent.create({
      data: {
        projectId: project.id,
        step: 'pipeline',
        status: 'running',
        message: `Project created (${input.mode === 'ugc' ? 'UGC ad' : 'topic'} mode, ${input.durationTarget}s, ${input.platform})`,
      },
    })

    runPipeline(project.id)

    const refreshed = await db.videoProject.findUnique({
      where: { id: project.id },
      include: { scenes: true, events: true },
    })
    return NextResponse.json(
      { project: toProjectDTO(refreshed ?? project) },
      { status: 201 }
    )
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to create project' },
      { status: 500 }
    )
  }
}
