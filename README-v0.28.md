# NahaLabs Reactivate v0.28

Reactivate now connects a seller-qualified prospect directly to a guarded campaign workflow.

## Run backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

## Important
The automated campaign endpoint requires `qualification_status=QUALIFIED`. It will not duplicate an active campaign. Content still pauses for human approval, and real platform publishing requires authenticated provider credentials.
