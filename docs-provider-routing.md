# Provider Routing Policy

NahaLabs owns the content domain and routing policy. Providers are replaceable adapters.

## Demo mode

`GENERATION_DEMO_MODE=true` keeps premium provider calls disabled unless explicitly enabled. This lets the team demonstrate the product using free/open-source processing and promotional/provider credits.

## Final polish

`polish_video` is reserved for the final creative polish stage. Higgsfield is selected only when enabled and permitted by the environment/plan policy.

## Production

The router should eventually consume a tenant plan + usage ledger before selecting a provider. Provider cost must never be trusted from the model; record actual provider usage from provider responses/invoices where available.
