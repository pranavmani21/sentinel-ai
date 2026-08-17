"""Deterministic incident fixtures used by tests, demos, and evaluations."""

from __future__ import annotations

import hashlib
import random
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from pathlib import Path

from sentinel_api.domain import (
    AuditAction,
    AuditRecord,
    DeploymentTelemetry,
    Evidence,
    EvidenceKind,
    GoldenIncidentDataset,
    Hypothesis,
    HypothesisStatus,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRun,
    LogTelemetry,
    MetricTelemetry,
    RunStatus,
    SourceKind,
    TelemetrySource,
)

GOLDEN_SEED = 20260818
GOLDEN_DATASET_PATH = Path(__file__).with_name("data") / "golden_incident.json"


def build_golden_incident(seed: int = GOLDEN_SEED) -> GoldenIncidentDataset:
    """Build one reproducible change-induced latency incident."""

    rng = random.Random(seed)
    base_time = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)
    incident_id = _stable_id("inc", seed, "checkout-latency")
    run_id = _stable_id("run", seed, "primary-investigation")

    prometheus = TelemetrySource(
        kind=SourceKind.METRICS,
        system="prometheus",
        locator="prometheus://platform/checkout-api",
    )
    loki = TelemetrySource(
        kind=SourceKind.LOGS,
        system="loki",
        locator="loki://production/checkout-api",
    )
    deployments = TelemetrySource(
        kind=SourceKind.DEPLOYMENTS,
        system="deployment-api",
        locator="deployments://production/checkout-api",
    )

    deployment = DeploymentTelemetry(
        id=_stable_id("tel", seed, "deployment"),
        incident_id=incident_id,
        source=deployments,
        observed_at=base_time - timedelta(minutes=12),
        service="checkout-api",
        version="2.4.0",
        commit_sha="4f19c2a",
        description="Raised database connection concurrency for promotion lookups.",
    )
    baseline_latency = MetricTelemetry(
        id=_stable_id("tel", seed, "baseline-latency"),
        incident_id=incident_id,
        source=prometheus,
        observed_at=base_time - timedelta(minutes=2),
        name="http.server.duration.p95",
        value=round(185 + rng.uniform(-5, 5), 2),
        unit="ms",
        labels={"service": "checkout-api", "route": "POST /checkout"},
    )
    elevated_latency = MetricTelemetry(
        id=_stable_id("tel", seed, "elevated-latency"),
        incident_id=incident_id,
        source=prometheus,
        observed_at=base_time + timedelta(minutes=2),
        name="http.server.duration.p95",
        value=round(1840 + rng.uniform(-25, 25), 2),
        unit="ms",
        labels={"service": "checkout-api", "route": "POST /checkout"},
    )
    pool_warning = LogTelemetry(
        id=_stable_id("tel", seed, "pool-warning"),
        incident_id=incident_id,
        source=loki,
        observed_at=base_time + timedelta(minutes=3),
        service="checkout-api",
        level="warning",
        message="Database connection acquisition exceeded the latency budget.",
        attributes={
            "pool_wait_ms": str(round(870 + rng.uniform(-20, 20), 2)),
            "request_id": f"req-{rng.randrange(100000, 999999)}",
        },
    )
    telemetry = (deployment, baseline_latency, elevated_latency, pool_warning)

    change_evidence = Evidence(
        id=_stable_id("evd", seed, "recent-change"),
        incident_id=incident_id,
        kind=EvidenceKind.CHANGE,
        summary="checkout-api 2.4.0 was deployed shortly before latency increased.",
        telemetry_ids=(deployment.id,),
        created_at=base_time + timedelta(minutes=5),
    )
    latency_evidence = Evidence(
        id=_stable_id("evd", seed, "latency-regression"),
        incident_id=incident_id,
        kind=EvidenceKind.SYMPTOM,
        summary="Checkout p95 latency increased by roughly an order of magnitude.",
        telemetry_ids=(baseline_latency.id, elevated_latency.id),
        created_at=base_time + timedelta(minutes=5, seconds=15),
    )
    pool_evidence = Evidence(
        id=_stable_id("evd", seed, "pool-contention"),
        incident_id=incident_id,
        kind=EvidenceKind.CORRELATION,
        summary="Connection acquisition delays coincide with elevated request latency.",
        telemetry_ids=(pool_warning.id, elevated_latency.id),
        created_at=base_time + timedelta(minutes=5, seconds=30),
    )
    evidence = (change_evidence, latency_evidence, pool_evidence)

    hypothesis = Hypothesis(
        id=_stable_id("hyp", seed, "deployment-caused-pool-contention"),
        incident_id=incident_id,
        statement=(
            "checkout-api 2.4.0 increased database concurrency, causing connection-pool "
            "contention and elevated checkout latency."
        ),
        status=HypothesisStatus.SUPPORTED,
        confidence=0.93,
        evidence_ids=tuple(item.id for item in evidence),
        created_at=base_time + timedelta(minutes=6),
        updated_at=base_time + timedelta(minutes=7),
    )
    run = InvestigationRun(
        id=run_id,
        incident_id=incident_id,
        status=RunStatus.COMPLETED,
        started_at=base_time + timedelta(minutes=4),
        completed_at=base_time + timedelta(minutes=9),
        evidence_ids=tuple(item.id for item in evidence),
        hypothesis_ids=(hypothesis.id,),
    )
    assert run.completed_at is not None
    incident = Incident(
        id=incident_id,
        title="Checkout latency after checkout-api 2.4.0",
        summary="Checkout requests are slow after a production deployment.",
        severity=IncidentSeverity.SEV2,
        status=IncidentStatus.INVESTIGATING,
        started_at=base_time,
        detected_at=base_time + timedelta(minutes=4),
        affected_services=("checkout-api", "payments-api"),
    )
    audit = (
        AuditRecord(
            id=_stable_id("aud", seed, "run-started"),
            incident_id=incident_id,
            run_id=run_id,
            action=AuditAction.RUN_STARTED,
            actor="sentinel-agent",
            occurred_at=run.started_at,
            target_type="run",
            target_id=run_id,
            details={"seed": str(seed)},
        ),
        AuditRecord(
            id=_stable_id("aud", seed, "evidence-recorded"),
            incident_id=incident_id,
            run_id=run_id,
            action=AuditAction.EVIDENCE_RECORDED,
            actor="sentinel-agent",
            occurred_at=base_time + timedelta(minutes=5, seconds=30),
            target_type="evidence",
            target_id=pool_evidence.id,
            details={"evidence_count": str(len(evidence))},
        ),
        AuditRecord(
            id=_stable_id("aud", seed, "hypothesis-recorded"),
            incident_id=incident_id,
            run_id=run_id,
            action=AuditAction.HYPOTHESIS_RECORDED,
            actor="sentinel-agent",
            occurred_at=hypothesis.created_at,
            target_type="hypothesis",
            target_id=hypothesis.id,
            details={"confidence": str(hypothesis.confidence)},
        ),
        AuditRecord(
            id=_stable_id("aud", seed, "run-completed"),
            incident_id=incident_id,
            run_id=run_id,
            action=AuditAction.RUN_COMPLETED,
            actor="sentinel-agent",
            occurred_at=run.completed_at,
            target_type="run",
            target_id=run_id,
            details={"result": "supported_hypothesis"},
        ),
    )

    return GoldenIncidentDataset(
        seed=seed,
        incident=incident,
        telemetry=telemetry,
        evidence=evidence,
        hypotheses=(hypothesis,),
        run=run,
        audit=audit,
    )


def serialize_golden_incident(seed: int = GOLDEN_SEED) -> str:
    """Serialize the deterministic dataset with stable formatting."""

    return build_golden_incident(seed).model_dump_json(indent=2) + "\n"


def load_golden_incident() -> GoldenIncidentDataset:
    """Load and validate the packaged golden dataset."""

    resource = files("sentinel_api").joinpath("data/golden_incident.json")
    return GoldenIncidentDataset.model_validate_json(resource.read_text(encoding="utf-8"))


def write_golden_incident(path: Path = GOLDEN_DATASET_PATH) -> Path:
    """Regenerate the checked-in dataset and return its path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_golden_incident(), encoding="utf-8", newline="\n")
    return path


def _stable_id(prefix: str, seed: int, label: str) -> str:
    """Derive a stable identifier without relying on global randomness."""

    digest = hashlib.sha256(f"sentinel:{seed}:{label}".encode()).hexdigest()[:16]
    return f"{prefix}_{digest}"


if __name__ == "__main__":
    print(write_golden_incident())
