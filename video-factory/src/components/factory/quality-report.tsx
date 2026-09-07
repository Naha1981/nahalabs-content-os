'use client'

import {
  AlertTriangle,
  CheckCircle2,
  MinusCircle,
  XCircle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import type { QualityCheck, QualityReport } from '@/lib/types'

function CheckIcon({ status }: { status: QualityCheck['status'] }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
    case 'warn':
      return <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
    case 'fail':
      return <XCircle className="h-4 w-4 text-red-400 shrink-0" />
    default:
      return <MinusCircle className="h-4 w-4 text-zinc-500 shrink-0" />
  }
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-zinc-400">{label}</span>
        <span className="font-mono text-zinc-300">{Math.round(value * 100)}%</span>
      </div>
      <Progress
        value={value * 100}
        className="h-1.5 bg-zinc-800 [&>div]:bg-amber-500"
      />
    </div>
  )
}

export function QualityReportCard({ report }: { report: QualityReport }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          Quality gate
          <span
            className={
              report.passed
                ? 'rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-400'
                : 'rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-400'
            }
          >
            {report.passed ? 'PASSED' : 'NEEDS REVIEW'}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="space-y-2">
          {report.checks.map((c) => (
            <li key={c.id} className="flex items-start gap-2">
              <CheckIcon status={c.status} />
              <div className="min-w-0">
                <p className="text-xs text-zinc-200">{c.label}</p>
                {c.detail && <p className="text-[11px] text-zinc-500">{c.detail}</p>}
              </div>
            </li>
          ))}
        </ul>
        <div className="space-y-2.5 pt-1 border-t border-zinc-800">
          <ScoreRow label="Technical" value={report.scores.technical} />
          {report.scores.visual != null && <ScoreRow label="Visual match" value={report.scores.visual} />}
          {report.scores.narration != null && (
            <ScoreRow label="Speech match" value={report.scores.narration} />
          )}
          <ScoreRow label="Overall" value={report.scores.overall} />
        </div>
        {report.transcriptCheck && (
          <p className="text-[11px] text-zinc-500 border-t border-zinc-800 pt-3">
            ASR spot-check (scene 1): “{report.transcriptCheck.transcript.slice(0, 120)}”
          </p>
        )}
      </CardContent>
    </Card>
  )
}
