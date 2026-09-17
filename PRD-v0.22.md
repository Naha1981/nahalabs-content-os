# NahaLabs Reactivate v0.22 — Voice + Captions Layer

## Goal
Turn a rendered vertical clip into a media asset with real voiceover and burned captions.

## Contract
Rendered video + production voiceover text -> local TTS WAV + SRT captions -> final MP4.

## Guardrails
- Never mark READY_TO_PUBLISH unless the final MP4 exists and is non-empty.
- Local eSpeak is explicitly labeled as the development/default provider.
- No network call is required for the local provider.
- Cloud TTS providers can replace the adapter later.
