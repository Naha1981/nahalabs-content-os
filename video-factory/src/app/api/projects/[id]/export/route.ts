import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { buildRemotionTsx, buildSrt, buildTimelineJson } from '@/lib/exports'
import { toProjectDTO } from '@/lib/serialize'

function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 48) || 'video'
  )
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const format = req.nextUrl.searchParams.get('format') ?? 'json'
    const row = await db.videoProject.findUnique({
      where: { id },
      include: { scenes: true, events: true },
    })
    if (!row) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 })
    }
    const project = toProjectDTO(row)
    const slug = slugify(project.title)

    if (format === 'srt') {
      const srt = buildSrt(project)
      return new NextResponse(srt || 'No caption tracks yet.', {
        headers: {
          'content-type': 'application/x-subrip; charset=utf-8',
          'content-disposition': `attachment; filename="${slug}.srt"`,
        },
      })
    }

    if (format === 'remotion') {
      const tsx = buildRemotionTsx(project)
      return new NextResponse(tsx, {
        headers: {
          'content-type': 'text/plain; charset=utf-8',
          'content-disposition': `attachment; filename="${slug}.tsx"`,
        },
      })
    }

    // default: timeline JSON bundle
    const json = buildTimelineJson(project)
    return new NextResponse(json, {
      headers: {
        'content-type': 'application/json; charset=utf-8',
        'content-disposition': `attachment; filename="${slug}-timeline.json"`,
      },
    })
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message ?? 'Export failed' },
      { status: 500 }
    )
  }
}
