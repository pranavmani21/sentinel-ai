# Golden incident fixture

`golden_incident.json` is the canonical Day 2 dataset for one change-induced checkout
latency incident. It contains an incident, provenance-bearing deployment/log/metric
telemetry, cited evidence, a supported hypothesis, one completed investigation run, and
its append-only audit trail.

The generator uses `GOLDEN_SEED = 20260818`, local `random.Random`, fixed UTC timestamps,
and SHA-256-derived identifiers. It never reads the wall clock or global random state.

Regenerate the serialized fixture from `backend/`:

```powershell
venv\Scripts\python -m sentinel_api.fixtures
```

`tests/test_domain.py` proves that the checked-in JSON matches the generator, round-trips
through the Pydantic schemas, contains provenance on every telemetry item, and rejects
dangling references.
