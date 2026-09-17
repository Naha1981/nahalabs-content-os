# NahaLabs Reactivate v0.19

v0.19 adds the first real media-rendering worker.

## Run backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

## Render flow
1. Create/approve a content asset.
2. Create a production brief.
3. Click **Render local preview**.
4. The API invokes local FFmpeg.
5. A real `.mp4` is stored and served from `/media/...`.

## Renderer
Provider: `LOCAL_FFMPEG_PREVIEW`

This is a deterministic preview renderer, not AI-generated UGC. A provider-specific video generator can be added behind the same render-job boundary later.

## Verification
Backend: 44/44 tests passing.
The sandbox could execute the renderer and API render flow successfully and produced a real MP4. Frontend Vite build remains unverified because installing frontend dependencies times out in the current sandbox environment.
