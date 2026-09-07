// Pure word-timing utilities — shared by the pipeline (server),
// the API routes and the browser player (client). No side effects.

import type { SubtitleTrack, WordTiming } from './types'

const WORDS_PER_SECOND = 2.55 // average narration pace used before audio probing

export function tokenize(text: string): string[] {
  return text
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .split(/\s+/)
    .map((w) => w.replace(/[^\p{L}\p{N}'.,!?\-–—%&$]/gu, ''))
    .map((w) => w.trim())
    .filter((w) => w.length > 0)
}

/** Rough duration estimate before the real audio duration is probed. */
export function estimateDuration(narration: string): number {
  const words = tokenize(narration)
  return Math.max(1.2, words.length / WORDS_PER_SECOND + 0.45)
}

/**
 * Distribute word timings across `duration` proportionally to word length.
 * This mirrors the WhisperX-style alignment concept: word-level captions
 * derived from the narration track, refined later against the real audio
 * duration once the browser probes it.
 */
export function distributeWords(words: string[], duration: number): WordTiming[] {
  if (words.length === 0) return []
  const weights = words.map((w) => w.length + 2.2)
  const total = weights.reduce((a, b) => a + b, 0)
  let acc = 0
  const out: WordTiming[] = []
  for (let i = 0; i < words.length; i++) {
    const start = (acc / total) * duration
    acc += weights[i]
    const end = (acc / total) * duration
    out.push({ w: words[i], s: round3(start), e: round3(end) })
  }
  // pad the first word slightly so it doesn't flash instantly
  if (out.length) out[0] = { ...out[0], s: round3(Math.min(out[0].s + 0.05, out[0].e)) }
  return out
}

export function buildSubtitleTrack(
  narration: string,
  duration: number | null,
  source: 'estimated' | 'probed'
): SubtitleTrack {
  const words = tokenize(narration)
  const dur = duration ?? estimateDuration(narration)
  return { source, duration: round3(dur), words: distributeWords(words, dur) }
}

/** Re-proportion existing word timings to a new measured duration. */
export function rescaleTrack(track: SubtitleTrack, newDuration: number): SubtitleTrack {
  if (track.duration <= 0 || newDuration <= 0) {
    return buildSubtitleTrack(track.words.map((w) => w.w).join(' '), newDuration, 'probed')
  }
  const k = newDuration / track.duration
  return {
    source: 'probed',
    duration: round3(newDuration),
    words: track.words.map((w) => ({
      w: w.w,
      s: round3(w.s * k),
      e: round3(w.e * k),
    })),
  }
}

/** Group words into caption cues of at most `maxWords` words. */
export function cueGroups(words: WordTiming[], maxWords = 5): WordTiming[][] {
  const cues: WordTiming[][] = []
  for (let i = 0; i < words.length; i += maxWords) {
    cues.push(words.slice(i, i + maxWords))
  }
  return cues
}

function round3(n: number): number {
  return Math.round(n * 1000) / 1000
}
