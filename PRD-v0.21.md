# NahaLabs Reactivate v0.21 — Media Assembly

## Goal
Combine multiple verified rendered clips into one publish-ready vertical MP4 without falsely claiming AI generation.

## Scope
- Assemble 1–10 locally rendered MP4 clips.
- Validate that every selected job belongs to the prospect and has a local rendered media URL.
- Concatenate clips with FFmpeg and normalize to 720x1280, 24fps, H.264/yuv420p.
- Return a real `/media/...` MP4 URL.
- Keep provider metadata explicit: `LOCAL_FFMPEG_ASSEMBLER`.

## Boundary
This version does not synthesize new AI footage, download arbitrary remote media, add licensed music, or publish automatically. KIE-generated remote URLs require a future media-download/staging adapter before assembly.
