from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from app.domain.contracts import GenerationProvider, GenerationRequest, GenerationResult
from app.providers.kie import KIEProvider

@dataclass
class GenerationRouter:
    providers: dict[str, GenerationProvider]
    default_provider: str = 'kie'

    @classmethod
    def production(cls) -> 'GenerationRouter':
        return cls(providers={'kie': KIEProvider()})

    def provider(self, name: str | None = None) -> GenerationProvider:
        selected = name or self.default_provider
        try:
            return self.providers[selected]
        except KeyError as exc:
            raise ValueError(f'Unknown generation provider: {selected}') from exc

    def submit(self, request: GenerationRequest, provider: str | None = None) -> GenerationResult:
        return self.provider(provider).submit(request)

    def status(self, provider_job_id: str, provider: str) -> GenerationResult:
        return self.provider(provider).status(provider_job_id)
