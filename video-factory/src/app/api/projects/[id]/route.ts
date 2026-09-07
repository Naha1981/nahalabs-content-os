import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { removeProjectAssets } from '@/lib/assets'
import { isPipelineRunning } from '@/lib/pipeline'
import { toProjectDTO } from '@/lib/serialize'

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const project = await db.videoProject.findUnique({
      where: { id },
      include: { scenes: true, events: true },
    })
    if (!project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 })
    }
    return NextResponse.json({
      project: toProjectDTO(project),
      running: isPipelineRunning(id),
    })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to load project' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const project = await db.videoProject.findUnique({ where: { id } })
    if (!project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 })
    }
    await db.videoProject.delete({ where: { id } })
    await removeProjectAssets(id).catch(() => undefined)
    return NextResponse.json({ ok: true })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to delete project' },
      { status: 500 }
    )
  }
}
