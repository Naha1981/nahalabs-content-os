# v1.4 — Creative Generation Orchestrator

The production state machine is now:

`queued → provider_processing → (polishing) → quality_review`

Failure state: `failed`.

## Provider policy

- KIE is the default generation provider.
- Higgsfield is only invoked when `polish_requested=true` and routing policy permits it.
- Provider-specific payloads stay inside adapters.
- GeneratedAsset stores provider job IDs and normalized output metadata.

## Source media

When a ContentPack has source media, the orchestrator creates a short-lived signed URL and passes it to the generation provider. Fully generative briefs can run without source media.

## Quality gate boundary

The orchestrator deliberately stops at `quality_review`. A separate media/quality worker should download or fetch the provider output, inspect media dimensions/codecs/duration, run deterministic checks, then mark the asset `approved` or `rejected`. This prevents an unverified remote URL from being treated as a publishable asset.

## Final polish

Higgsfield is the final optional polish stage. It receives the generated output, not the original source footage, preserving the architecture's intended sequence: generation → polish → quality → approval → publishing.
