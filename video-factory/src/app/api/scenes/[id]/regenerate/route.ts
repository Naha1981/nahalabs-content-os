import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { db } from '@/lib/db'
import { regenerateScene } from '@/lib/pipeline'

const regenSchema = z.object({
  target: z.enum(['image', 'audio']),
})

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await req.json()
    const parsed = regenSchema.safeParse(body)
    if (!parsed.success) {
      return NextResponse.json({ error: 'target must be "image" or "audio"' }, { status: 400 })
    }
    const scene = await db.videoScene.findUnique({ where: { id } })
    if (!scene) {
      return NextResponse.json({ error: 'Scene not found' }, { status: 404 })
    }
    if (parsed.data.target === 'audio' && scene.narration.trim().length === 0) {
      return NextResponse.json({ error: 'Scene has no narration to speak' }, { status: 400 })
    }
    regenerateScene(id, parsed.data.target)
    return NextResponse.json({ ok: true })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to regenerate' },
      { status: 500 }
    )
  }
}
