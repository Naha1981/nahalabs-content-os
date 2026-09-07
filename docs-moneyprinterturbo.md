# MoneyPrinterTurbo integration

NahaLabs Content OS now has an optional `moneyprinterturbo` generation adapter.

MoneyPrinterTurbo is used as an **execution engine**, not as the application's source of truth. NahaLabs continues to own tenant isolation, creative briefs, approvals, storage, quality gates, publishing and analytics. MPT supplies its end-to-end script/material/TTS/subtitle/video assembly pipeline.

## Enable locally

1. Clone the upstream project into a worker environment.
2. Configure MPT's own provider/material settings there.
3. Set:

```env
MPT_ENABLED=true
MPT_ROOT=/opt/MoneyPrinterTurbo
MPT_PYTHON=python
MPT_TIMEOUT_SECONDS=1200
```

4. Generate an asset with `provider=moneyprinterturbo`.

The NahaLabs worker downloads approved source media into a temporary directory when source footage exists, passes the creative brief to MPT, uploads the completed MP4 to private S3, and then sends the resulting asset through the normal NahaLabs quality/approval flow.

## Why this is optional

MPT is a substantial standalone application with its own configuration and external provider requirements. Keeping it behind a provider adapter lets NahaLabs use it where it is strongest without coupling every customer or deployment to its dependency footprint.

## Upstream

The upstream project is MIT licensed and provides CLI/API/WebUI workflows for automated short-video generation. See the official repository for the current CLI contract and provider support.
