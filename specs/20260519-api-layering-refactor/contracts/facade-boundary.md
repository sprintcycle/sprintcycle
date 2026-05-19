# Façade boundary contract

`SprintCycle` in `sprintcycle/api.py` MUST:

1. Expose stable public methods for Dashboard, REST, and SDK.
2. Delegate workflow logic to `application/services/*`.
3. Not import persistence details except through service constructors.
4. Not assemble large lifecycle payloads inline.

Violations: orchestration blocks > 20 lines in `api.py`, direct registry calls outside wiring.
