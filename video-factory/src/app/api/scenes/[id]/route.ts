import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { db } from '@/lib/db'
import { buildSubtitleTrack, rescaleTrack } from '@/lib/subtitles'
import type { SubtitleTrack } from '@/lib/types'
import { toSceneDTO } from '@/lib/serialize'

const patchSchema = z.object({
  narration: z.string().trim().min(1).max(950).optional(),
  onScreenText: z.string().trim().max(80).nullable().optional(),
  audioDuration: z.number().positive().max(600).optional(),
})

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()
    const parsed = patchSchema.safeParse(body)
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Invalid request', issues: parsed.error.issues.map((i) => i.message) },
        { status: 400 }
      )
    }
    const input = parsed.data

    const scene = await db.videoScene.findUnique({ where: { id } })
    if (!scene) {
      return NextResponse.json({ error: 'Scene not found' }, { status: 404 })
    }

    const data: Record<string, unknown> = {}

    if (input.narration !== undefined && input.narration !== scene.narration) {
      data.narration = input.narration
      // narration changed: existing audio/subtitles are stale until regenerated
      data.audioStatus = scene.audioUrl ? 'pending' : 'pending'
      data.subtitlesJson = JSON.stringify(
        buildSubtitleTrack(input.narration, null, 'estimated')
      )
    }

    if (input.onScreenText !== undefined) {
      data.onScreenText = input.onScreenText || null
    }

    if (input.audioDuration !== undefined && scene.audioUrl) {
      const existing: SubtitleTrack | null = scene.subtitlesJson
        ? JSON.parse(scene.subtitlesJson)
        : null
      const track = existing
        ? rescaleTrack(existing, input.audioDuration)
        : buildSubtitleTrack(scene.narration, input.audioDuration, 'probed')
      data.audioDuration = input.audioDuration
      data.subtitlesJson = JSON.stringify(track)
    }

    if (Object.keys(data).length === 0) {
      return NextResponse.json({ scene: toSceneDTO(scene) })
    }

    const updated = await db.videoScene.update({ where: { id }, data })
    return NextResponse.json({ scene: toSceneDTO(updated) })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to update scene' },
      { status: 500 }
    )
  }
}
