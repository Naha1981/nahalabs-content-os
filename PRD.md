# NahaLabs Reactivate v0.16 — Content Source Ingestion

## Goal
Make PatternVault usable from real source material without pretending that arbitrary social video URLs can be transcribed when the runtime cannot access the media.

## Inputs
1. Public HTTP/HTTPS URL: fetch readable HTML and extract page text.
2. Supplied transcript/text: analyse directly.
3. Text/Markdown/JSON upload: analyse directly.

## Output
A persisted PatternVault record containing the extracted hook, promise, structure, CTA, angle, audience, format and emotional trigger, plus explicit ingestion/extraction status.

## Safety / truthfulness
- No fabricated transcript.
- Unsupported binary/video pages are explicitly marked.
- URL fetch errors are returned to the caller.
- Source URL remains attached to the saved pattern.
