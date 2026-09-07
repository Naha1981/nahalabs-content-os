import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { isPipelineRunning, runPipeline } from '@/lib/pipeline'

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const project = await db.videoProject.findUnique({ where: { id } })
    if (!project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 })
    }
    if (isPipelineRunning(id)) {
      return NextResponse.json({ ok: true, message: 'Pipeline already running' })
    }
    // Idempotent resume: completed steps skip, failed/pending assets regenerate,
    // the quality gate re-runs at the end.
    await db.videoProject.update({
      where: { id },
      data: { status: 'queued', error: null, stepDetail: null },
    })
    runPipeline(id)
    return NextResponse.json({ ok: true })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Failed to resume pipeline' },
      { status: 500 }
    )
  }
}
