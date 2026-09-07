# Media Worker v0.7

The media worker handles deterministic media work outside the API process.

## Supported output profiles
- 9:16 — 1080x1920
- 1:1 — 1080x1080
- 16:9 — 1920x1080
- 4:5 — 1080x1350

## Current pipeline
S3/local input → FFmpeg render → optional SRT captions → H.264/AAC delivery file → ffprobe validation.

## Production deployment
Run this worker in an ECS/Fargate container with FFmpeg installed. SQS should deliver render jobs; the worker must acknowledge only after the output is durably stored and the database job state is committed. Use a DLQ for poison jobs.

## Important boundary
Background replacement, generative scene transformation, and generative B-roll remain provider operations. They should happen before this deterministic final render or as an explicit transformation stage, never by silently modifying source media.
