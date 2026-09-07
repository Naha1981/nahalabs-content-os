// NahaLabs Content OS — Video Factory provider layer.
//
// Mirrors the content-engine backend (app/providers + app/services/generation_router.py):
// generation happens behind replaceable adapters selected by operation, so the
// domain never talks to a specific vendor SDK.
//
//   GenerationProvider.protocol  ->  ProviderAdapter (name + supported operations)
//   GenerationRouter.choose(op)  ->  RouteDecision { provider, reason }
//
// Default route: the z-ai SDK (search, page reading, LLM, images, TTS, ASR, VLM).
// Bring-your-own-GPU-box route: set VIDEO_FACTORY_IMAGE_ENDPOINT to any HTTP
// endpoint implementing { prompt, size } -> { image_base64 } and image.generate
// routes there instead (e.g. a ComfyUI / Wan 2.2 / HunyuanVideo gateway you host).
// Everything else stays on the default route until you add an adapter.

import ZAI from 'z-ai-web-dev-sdk'

export type Operation =
  | 'web.search'
  | 'web.read'
  | 'text.generate'
  | 'image.generate'
  | 'speech.synthesize'
  | 'speech.transcribe'
  | 'vision.analyze'

export interface RouteDecision {
  provider: string
  reason: string
}

export interface ProviderAdapter {
  name: string
  operations: Operation[]
}

export interface ChatMessage {
  role: 'assistant' | 'user'
  content: string
}

export interface SearchResultItem {
  url: string
  name: string
  snippet: string
  host_name: string
  date?: string
}

export interface PageContent {
  title: string
  url: string
  html: string
}

export interface ImageAnalysisInput {
  dataUrl: string
  prompt: string
}

const ZAI_OPERATIONS: Operation[] = [
  'web.search',
  'web.read',
  'text.generate',
  'image.generate',
  'speech.synthesize',
  'speech.transcribe',
  'vision.analyze',
]

type ZAIClient = Awaited<ReturnType<typeof ZAI.create>>

export class GenerationRouter {
  private client: Promise<ZAIClient> | null = null

  readonly providers: ProviderAdapter[] = [
    { name: 'zai', operations: ZAI_OPERATIONS },
    {
      name: 'remote-http',
      operations: ['image.generate'],
    },
  ]

  private zai(): Promise<ZAIClient> {
    this.client ??= ZAI.create()
    return this.client
  }

  /** Route decision for an operation — same idea as GenerationRouter.choose(). */
  choose(operation: Operation): RouteDecision {
    if (operation === 'image.generate' && process.env.VIDEO_FACTORY_IMAGE_ENDPOINT) {
      return {
        provider: 'remote-http',
        reason: 'VIDEO_FACTORY_IMAGE_ENDPOINT is configured — routing to your GPU box',
      }
    }
    return { provider: 'zai', reason: 'default route' }
  }

  async search(query: string, num = 8): Promise<SearchResultItem[]> {
    const zai = await this.zai()
    const results = (await zai.functions.invoke('web_search', {
      query,
      num,
    })) as SearchResultItem[]
    return Array.isArray(results) ? results : []
  }

  async readPage(url: string): Promise<PageContent> {
    const zai = await this.zai()
    const result = (await zai.functions.invoke('page_reader', { url })) as {
      data: { title: string; url: string; html: string }
    }
    return {
      title: result?.data?.title ?? url,
      url: result?.data?.url ?? url,
      html: result?.data?.html ?? '',
    }
  }

  async generateText(messages: ChatMessage[]): Promise<string> {
    const zai = await this.zai()
    return withRateRetry(async () => {
      const completion = await zai.chat.completions.create({
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
        thinking: { type: 'disabled' },
      })
      const content = completion.choices[0]?.message?.content
      if (!content || !content.trim()) throw new Error('LLM returned an empty response')
      return content
    })
  }

  /** Structured JSON generation with one retry (LLMs sometimes wrap JSON in prose/fences). */
  async generateStructuredJson<T>(messages: ChatMessage[]): Promise<T> {
    for (let attempt = 0; attempt < 2; attempt++) {
      const raw = await this.generateText(messages)
      try {
        return extractJson<T>(raw)
      } catch (err) {
        if (attempt === 1) {
          throw new Error(
            `Could not parse structured JSON from LLM output: ${(err as Error).message}`
          )
        }
        await new Promise((r) => setTimeout(r, 400))
      }
    }
    throw new Error('unreachable')
  }

  async generateImage(prompt: string, size = '768x1344'): Promise<{ base64: string; provider: string }> {
    const decision = this.choose('image.generate')
    if (decision.provider === 'remote-http') {
      const endpoint = process.env.VIDEO_FACTORY_IMAGE_ENDPOINT as string
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ prompt, size }),
      })
      if (!res.ok) {
        throw new Error(`remote image endpoint ${endpoint} responded ${res.status}`)
      }
      const data = (await res.json()) as { image_base64?: string; base64?: string }
      const base64 = data.image_base64 ?? data.base64
      if (!base64) throw new Error('remote image endpoint returned no image_base64')
      return { base64, provider: decision.provider }
    }
    const zai = await this.zai()
    return withRateRetry(async () => {
      const response = await zai.images.generations.create({ prompt, size })
      const base64 = response?.data?.[0]?.base64
      if (!base64) throw new Error('image generation returned no data')
      return { base64, provider: 'zai' }
    })
  }

  async synthesizeSpeech(input: {
    text: string
    voice: string
    speed: number
    format?: 'wav'
  }): Promise<Buffer> {
    // NOTE: the live TTS API rejects response_format "mp3" with error 1214 —
    // "wav" is the supported non-streaming format (verified against the API).
    const zai = await this.zai()
    return withRateRetry(
      async () => {
        const response = await zai.audio.tts.create({
          input: input.text,
          voice: input.voice,
          speed: input.speed,
          response_format: 'wav',
          stream: false,
        })
        const arrayBuffer = await response.arrayBuffer()
        const buffer = Buffer.from(new Uint8Array(arrayBuffer))
        if (buffer.length === 0) throw new Error('TTS returned empty audio')
        return buffer
      },
      4
    )
  }

  async transcribeAudio(buffer: Buffer): Promise<string> {
    const zai = await this.zai()
    return withRateRetry(async () => {
      const response = await zai.audio.asr.create({
        file_base64: buffer.toString('base64'),
      })
      const text = (response as { text?: string })?.text ?? ''
      if (!text.trim()) throw new Error('ASR returned empty transcript')
      return text
    })
  }

  async analyzeImages(images: ImageAnalysisInput[], instruction: string): Promise<string> {
    const zai = await this.zai()
    return withRateRetry(async () => {
      const content: Array<Record<string, unknown>> = [
        { type: 'text', text: instruction },
      ]
      for (const img of images) {
        content.push({ type: 'image_url', image_url: { url: img.dataUrl } })
      }
      const response = await zai.chat.completions.createVision({
        messages: [{ role: 'user', content: content as never }],
        thinking: { type: 'disabled' },
      })
      const text = response.choices[0]?.message?.content
      if (!text) throw new Error('vision analysis returned no content')
      return text
    })
  }
}

function extractJson<T>(raw: string): T {
  let text = raw.trim()
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fence) text = fence[1].trim()
  const start = text.indexOf('{')
  const startArr = text.indexOf('[')
  const effectiveStart =
    start === -1 ? startArr : startArr === -1 ? start : Math.min(start, startArr)
  const endObj = text.lastIndexOf('}')
  const endArr = text.lastIndexOf(']')
  const effectiveEnd = Math.max(endObj, endArr)
  if (effectiveStart >= 0 && effectiveEnd > effectiveStart) {
    text = text.slice(effectiveStart, effectiveEnd + 1)
  }
  return JSON.parse(text) as T
}

// Module-level singleton (NOT globalThis): a globalThis cache survives Turbopack
// HMR and keeps serving pre-fix module code; module scope re-evaluates on reload.
// Behavior in production is identical.
let routerInstance: GenerationRouter | null = null

/** Retry helper for transient 429s — the upstream APIs rate-limit bursts. */
async function withRateRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  let lastErr: unknown
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      const msg = (err as Error).message ?? ''
      const rateLimited =
        msg.includes('429') || msg.toLowerCase().includes('too many requests')
      if (rateLimited && i < attempts - 1) {
        // per-minute quota windows: wait long enough for the window to roll
        await new Promise((r) => setTimeout(r, 5000 * (i + 1)))
        continue
      }
      throw err
    }
  }
  throw lastErr
}

export function getRouter(): GenerationRouter {
  routerInstance ??= new GenerationRouter()
  return routerInstance
}
