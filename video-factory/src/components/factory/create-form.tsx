'use client'

import { useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { PLATFORMS, STYLES, VOICES } from '@/lib/types'

export interface CreatePayload {
  topic: string
  mode: 'topic' | 'ugc'
  productUrl?: string
  platform: string
  style: string
  voice: string
  speed: number
  durationTarget: number
}

export function CreateForm({
  creating,
  onCreate,
}: {
  creating: boolean
  onCreate: (payload: CreatePayload) => void
}) {
  const [mode, setMode] = useState<'topic' | 'ugc'>('topic')
  const [topic, setTopic] = useState('')
  const [productUrl, setProductUrl] = useState('')
  const [platform, setPlatform] = useState('tiktok')
  const [style, setStyle] = useState('educational')
  const [voice, setVoice] = useState('tongtong')
  const [duration, setDuration] = useState(30)
  const [error, setError] = useState<string | null>(null)

  function submit() {
    setError(null)
    const trimmed = topic.trim()
    if (trimmed.length < 3) {
      setError('Give the factory a topic or keyword to work with (at least 3 characters).')
      return
    }
    if (mode === 'ugc') {
      const url = productUrl.trim()
      if (!url || !/^https?:\/\/.+\..+/.test(url)) {
        setError('UGC ad mode needs a product URL (e.g. a Shopify or Amazon product page).')
        return
      }
      onCreate({
        topic: trimmed,
        mode,
        productUrl: url,
        platform,
        style: 'ugc',
        voice,
        speed: 1.0,
        durationTarget: duration,
      })
      return
    }
    onCreate({
      topic: trimmed,
      mode,
      platform,
      style,
      voice,
      speed: 1.0,
      durationTarget: duration,
    })
  }

  return (
    <Card className="border-zinc-800 bg-zinc-900/60">
      <CardContent className="p-4 sm:p-6 space-y-5">
        <Tabs value={mode} onValueChange={(v) => setMode(v as 'topic' | 'ugc')}>
          <TabsList className="grid w-full grid-cols-2 bg-zinc-800/80">
            <TabsTrigger value="topic">Topic → Video</TabsTrigger>
            <TabsTrigger value="ugc">Product URL → UGC Ad</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="space-y-2">
          <Label htmlFor="topic" className="text-zinc-300">
            {mode === 'topic' ? (
              <>What should the video be about?</>
            ) : (
              <>What is the ad about? <span className="text-zinc-500">(used alongside the product page)</span></>
            )}
          </Label>
          {mode === 'topic' ? (
            <Textarea
              id="topic"
              placeholder="e.g. Why Cape Town restaurants are winning with short-form video"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={2}
              className="resize-none bg-zinc-950 border-zinc-800 focus-visible:ring-amber-500/40"
            />
          ) : (
            <div className="space-y-2">
              <Input
                placeholder="https://your-store.com/products/the-product"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                className="bg-zinc-950 border-zinc-800 focus-visible:ring-amber-500/40"
              />
              <Input
                placeholder="Optional notes: product name, offer, audience…"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="bg-zinc-950 border-zinc-800 focus-visible:ring-amber-500/40"
              />
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-zinc-400">Platform</Label>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger className="bg-zinc-950 border-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PLATFORMS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-zinc-400">Style</Label>
            <Select value={style} onValueChange={setStyle} disabled={mode === 'ugc'}>
              <SelectTrigger className="bg-zinc-950 border-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STYLES.filter((s) => mode !== 'ugc' || s.value === 'ugc').map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5 col-span-2 sm:col-span-1">
            <Label className="text-xs text-zinc-400">Voice</Label>
            <Select value={voice} onValueChange={setVoice}>
              <SelectTrigger className="bg-zinc-950 border-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {VOICES.map((v) => (
                  <SelectItem key={v.value} value={v.value}>
                    {v.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-zinc-400">Target duration</Label>
            <span className="text-xs font-mono text-amber-400">{duration}s</span>
          </div>
          <Slider
            value={[duration]}
            min={15}
            max={60}
            step={5}
            onValueChange={([v]) => setDuration(v)}
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <Button
          onClick={submit}
          disabled={creating}
          className="w-full h-11 text-base font-semibold"
          size="lg"
        >
          {creating ? (
            <>
              <Loader2 className="animate-spin" /> Starting pipeline…
            </>
          ) : (
            <>
              <Sparkles /> Generate video
            </>
          )}
        </Button>
        <p className="text-xs text-zinc-500 text-center">
          Research → script → visuals → narration → captions → quality gate. Runs live, ~2-3 minutes.
        </p>
      </CardContent>
    </Card>
  )
}
