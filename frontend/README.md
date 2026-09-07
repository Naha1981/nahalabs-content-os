# NahaLabs Content OS — Customer Demo Frontend

Next.js customer-facing MVP surface for the v1.8 backend.

## Flow

1. Create/identify business
2. Create a content pack
3. Review generated assets
4. Approve selected assets
5. Connect social accounts
6. Preflight + schedule/publish
7. Learn from analytics

The current UI runs in demo mode so it can be shown to restaurants without live provider credentials. Replace the local actions with the FastAPI endpoints as the integration layer is wired.

## Run

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` when wiring the UI to the FastAPI service.
