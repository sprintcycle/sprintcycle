# Evolution Changelog

## v0.9.0 - Architecture Simplification

- Removed GEPA standalone engine and GEPAClient
- Removed Hermes agent dependency
- All evolution now runs through `EvolutionPipeline`
- Removed Pareto optimization (replaced with simple evaluation dimensions)
- Config unified into `RuntimeConfig` and `SprintCycleConfig`
- `LEVEL_3_GEPA` → `LEVEL_3_LLM` in error router

## Earlier Versions

Archived. See git history for details.
