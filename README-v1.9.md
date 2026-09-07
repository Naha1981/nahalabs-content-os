# NahaLabs Content OS v1.9

Final MVP engineering package for restaurant demonstrations and first paid pilots.

## Customer promise

**Shoot once. Get a month of content.**

## Included

- FastAPI production backend
- Content intelligence + adaptive strategy
- KIE generation routing
- Optional Higgsfield final polish
- Quality gate
- Zernio preflight + publishing
- Approval boundary
- Publishing idempotency/reconciliation
- Analytics learning loop
- Next.js customer demo workspace
- Safe demo/live frontend mode
- Frontend Docker image

## Run the frontend demo

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Keep `NEXT_PUBLIC_DEMO_MODE=true` for a credential-free demonstration.

## Run the API

```bash
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API requires the infrastructure settings defined in `.env.example`.

## Important

The frontend demo mode intentionally does not call live providers. Before enabling live mode, wire Cognito authentication and verify the complete approval → preflight → publish flow with a test social account.
