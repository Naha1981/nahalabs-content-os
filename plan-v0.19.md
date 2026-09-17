# Reactivate v0.19 build plan

1. Create renderer adapter with explicit `LOCAL_FFMPEG_PREVIEW` provider.
2. Render a real MP4 from the production brief.
3. Persist renderer status, errors and rendered timestamp.
4. Expose `/api/v1/production-jobs/{job_id}/render`.
5. Serve generated media through `/media`.
6. Add UI render/preview/download controls.
7. Test renderer, storage migration, API render flow and media retrieval.
8. Keep AI generation provider integration for a later provider-specific version.
