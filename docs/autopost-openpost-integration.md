# AutoPost × OpenPost Integration Boundary

## Decision

Do not replace the NahaLabs Content OS wholesale with OpenPost.

The current repository already contains the expensive NahaLabs-specific layer: adaptive content intelligence, strategy context, provider-neutral generation, KIE.ai routing, Higgsfield polish, FFmpeg rendering, quality gates, publishing preflight, reconciliation workers and the Video Factory.

OpenPost should supply the execution pattern for the final-mile publishing product.

## Capability split

| Capability | NahaLabs | AutoPost/OpenPost layer |
|---|---|---|
| Brand DNA | Own | Consume |
| Content strategy | Own | Consume |
| Winning-content learning | Own | Consume |
| Creative briefs | Own | Consume |
| Image/video/audio generation | Own | Consume finished media |
| Quality gate | Own | Enforce before publish |
| Publication object | Adapter/boundary | Own execution model |
| Platform rendition | Strategy + adapter input | Own destination lifecycle |
| Scheduling | Existing publishing worker | Target canonical scheduler |
| Provider account readiness | Existing adapters | Target canonical account model |
| Media library | Existing S3/media layer | Target unified media surface |
| Analytics | Existing learning layer | Consume published metrics |
| MCP/API automation | NahaLabs orchestration | Target execution surface |

## OpenPost facts verified

OpenPost exposes publication create/edit/rendition/schedule/publish-now/retry operations through its API-token surface. Its MCP surface includes publication creation, listing, validation, scheduling and cancellation. It uses the same workspace authorization model across its clients.

OpenPost is AGPL-3.0-only. Any direct incorporation or modification must retain the applicable license and source-availability obligations.

## Implementation sequence

1. Keep the current NahaLabs core intact.
2. Define an `AutoPostPublisher` contract in NahaLabs.
3. Add an OpenPost HTTP adapter behind that contract.
4. Map `CreativeBrief` + `GeneratedAsset` into an OpenPost Publication and destination renditions.
5. Keep NahaLabs quality/approval as the gate before mutation calls.
6. Reconcile OpenPost publication events back into NahaLabs analytics.
7. Add MCP automation only after the HTTP boundary is tested.
8. Replace duplicated NahaLabs scheduling/publishing paths only after parity tests pass.

## Non-goals

- Do not copy OpenPost's entire codebase into the NahaLabs backend merely to get a scheduler.
- Do not duplicate social-provider credentials in two systems.
- Do not bypass NahaLabs quality/approval controls.
- Do not remove OpenPost AGPL notices.

## Success condition

A NahaLabs user should be able to go from a business objective to a generated, quality-approved, platform-adapted and scheduled publication without manually moving assets between systems.
