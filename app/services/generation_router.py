from __future__ import annotations
from dataclasses import dataclass
from app.core.config import get_settings
from app.providers.contracts import GenerationProvider, GenerationRequest, GenerationResult
from app.providers.kie import KIEProvider
from app.providers.higgsfield import HiggsfieldProvider
from app.providers.money_printer_turbo import MoneyPrinterTurboProvider

@dataclass(frozen=True)
class RouteDecision:
    provider: str
    reason: str
    estimated_cost: float = 0.0

class GenerationRouter:
    """Selects providers using product policy; providers remain replaceable adapters."""
    def __init__(self, providers: list[GenerationProvider] | None = None) -> None:
        s = get_settings()
        self.demo_mode = s.generation_demo_mode
        self.max_cost = s.generation_max_cost_per_asset
        self.higgsfield_demo_enabled = s.higgsfield_demo_enabled
        self.providers = providers or [KIEProvider(), HiggsfieldProvider(), MoneyPrinterTurboProvider()]

    def choose(self, request: GenerationRequest) -> RouteDecision:
        candidates = [p for p in self.providers if p.supports(request.operation)]
        requested = str(request.metadata.get("requested_provider", "")).strip().lower()
        if requested:
            selected = next((p for p in self.providers if p.name == requested), None)
            if selected is None:
                raise ValueError(f"Unknown generation provider: {requested}")
            if not selected.supports(request.operation):
                raise ValueError(f"Generation provider is disabled or unsupported: {requested}")
            return RouteDecision(selected.name, "explicit_provider_selection")
        if not candidates:
            raise ValueError(f"No provider supports operation={request.operation}")
        if request.operation == "polish_video":
            hf = next((p for p in candidates if p.name == "higgsfield"), None)
            if hf and (not self.demo_mode or self.higgsfield_demo_enabled):
                return RouteDecision("higgsfield", "final_polish")
            raise ValueError("Higgsfield final polish is disabled")
        kie = next((p for p in candidates if p.name == "kie"), candidates[0])
        return RouteDecision(kie.name, "default_generation_route")

    async def submit(self, request: GenerationRequest) -> GenerationResult:
        decision = self.choose(request)
        provider = next(p for p in self.providers if p.name == decision.provider)
        return await provider.submit(request)

    async def status(self, provider: str, provider_job_id: str) -> GenerationResult:
        target = next(p for p in self.providers if p.name == provider)
        return await target.status(provider_job_id)
