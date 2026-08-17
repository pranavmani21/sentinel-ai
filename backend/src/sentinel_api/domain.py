"""Validated domain contracts for incidents and their investigation trail."""

from collections.abc import Iterable
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

IncidentId = Annotated[str, Field(pattern=r"^inc_[0-9a-f]{16}$")]
TelemetryId = Annotated[str, Field(pattern=r"^tel_[0-9a-f]{16}$")]
EvidenceId = Annotated[str, Field(pattern=r"^evd_[0-9a-f]{16}$")]
HypothesisId = Annotated[str, Field(pattern=r"^hyp_[0-9a-f]{16}$")]
RunId = Annotated[str, Field(pattern=r"^run_[0-9a-f]{16}$")]
AuditId = Annotated[str, Field(pattern=r"^aud_[0-9a-f]{16}$")]


class DomainModel(BaseModel):
    """Base model that rejects unknown fields and accidental mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class IncidentSeverity(StrEnum):
    """Customer-impact severity used for incident prioritization."""

    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"


class IncidentStatus(StrEnum):
    """Lifecycle state of an incident."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class SourceKind(StrEnum):
    """Supported telemetry source categories."""

    LOGS = "logs"
    METRICS = "metrics"
    DEPLOYMENTS = "deployments"


class EvidenceKind(StrEnum):
    """How an evidence record contributes to an investigation."""

    CHANGE = "change"
    SYMPTOM = "symptom"
    CORRELATION = "correlation"


class HypothesisStatus(StrEnum):
    """Evaluation state of a hypothesis."""

    PROPOSED = "proposed"
    SUPPORTED = "supported"
    REJECTED = "rejected"


class RunStatus(StrEnum):
    """Execution state of an investigation run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditAction(StrEnum):
    """Append-only actions recorded during an investigation."""

    RUN_STARTED = "run_started"
    EVIDENCE_RECORDED = "evidence_recorded"
    HYPOTHESIS_RECORDED = "hypothesis_recorded"
    RUN_COMPLETED = "run_completed"


class TelemetrySource(DomainModel):
    """Origin metadata required for every telemetry datum."""

    kind: SourceKind
    system: str = Field(min_length=1)
    locator: str = Field(min_length=1)


class Incident(DomainModel):
    """An operational incident under investigation."""

    id: IncidentId
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    severity: IncidentSeverity
    status: IncidentStatus
    started_at: AwareDatetime
    detected_at: AwareDatetime
    affected_services: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_chronology(self) -> Self:
        """Detection cannot precede the incident's first known impact."""

        if self.detected_at < self.started_at:
            raise ValueError("detected_at must be on or after started_at")
        return self


class TelemetryBase(DomainModel):
    """Provenance shared by logs, metrics, and deployment events."""

    id: TelemetryId
    incident_id: IncidentId
    source: TelemetrySource
    observed_at: AwareDatetime


class LogTelemetry(TelemetryBase):
    """A structured log event."""

    kind: Literal["log"] = "log"
    service: str = Field(min_length=1)
    level: str = Field(min_length=1)
    message: str = Field(min_length=1)
    attributes: dict[str, str] = Field(default_factory=dict)


class MetricTelemetry(TelemetryBase):
    """A single metric observation."""

    kind: Literal["metric"] = "metric"
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    labels: dict[str, str] = Field(default_factory=dict)


class DeploymentTelemetry(TelemetryBase):
    """A deployment or change event."""

    kind: Literal["deployment"] = "deployment"
    service: str = Field(min_length=1)
    version: str = Field(min_length=1)
    commit_sha: str = Field(pattern=r"^[0-9a-f]{7,40}$")
    description: str = Field(min_length=1)


TelemetryItem = Annotated[
    LogTelemetry | MetricTelemetry | DeploymentTelemetry,
    Field(discriminator="kind"),
]


class Evidence(DomainModel):
    """A cited finding derived from one or more telemetry items."""

    id: EvidenceId
    incident_id: IncidentId
    kind: EvidenceKind
    summary: str = Field(min_length=1)
    telemetry_ids: tuple[TelemetryId, ...] = Field(min_length=1)
    created_at: AwareDatetime


class Hypothesis(DomainModel):
    """A testable explanation backed by explicit evidence."""

    id: HypothesisId
    incident_id: IncidentId
    statement: str = Field(min_length=1)
    status: HypothesisStatus
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: tuple[EvidenceId, ...] = Field(min_length=1)
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def validate_chronology(self) -> Self:
        """A hypothesis cannot be updated before it is created."""

        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be on or after created_at")
        return self


class InvestigationRun(DomainModel):
    """One bounded investigation execution."""

    id: RunId
    incident_id: IncidentId
    status: RunStatus
    started_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    evidence_ids: tuple[EvidenceId, ...] = ()
    hypothesis_ids: tuple[HypothesisId, ...] = ()

    @model_validator(mode="after")
    def validate_completion(self) -> Self:
        """Completed runs require a valid completion timestamp."""

        if self.status is RunStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed runs require completed_at")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must be on or after started_at")
        return self


class AuditRecord(DomainModel):
    """An immutable audit event emitted by an investigation run."""

    id: AuditId
    incident_id: IncidentId
    run_id: RunId
    action: AuditAction
    actor: str = Field(min_length=1)
    occurred_at: AwareDatetime
    target_type: Literal["incident", "run", "evidence", "hypothesis"]
    target_id: str = Field(min_length=1)
    details: dict[str, str] = Field(default_factory=dict)


class GoldenIncidentDataset(DomainModel):
    """Self-contained, cross-reference-validated incident fixture."""

    schema_version: Literal["1.0"] = "1.0"
    seed: int = Field(ge=0)
    incident: Incident
    telemetry: tuple[TelemetryItem, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    hypotheses: tuple[Hypothesis, ...] = Field(min_length=1)
    run: InvestigationRun
    audit: tuple[AuditRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        """Reject dangling, duplicate, or cross-incident references."""

        telemetry_ids = _unique_ids("telemetry", (item.id for item in self.telemetry))
        evidence_ids = _unique_ids("evidence", (item.id for item in self.evidence))
        hypothesis_ids = _unique_ids(
            "hypotheses",
            (item.id for item in self.hypotheses),
        )
        _unique_ids("audit", (item.id for item in self.audit))

        incident_id = self.incident.id
        if any(item.incident_id != incident_id for item in self.telemetry):
            raise ValueError("all telemetry must reference the dataset incident")
        if any(item.incident_id != incident_id for item in self.evidence):
            raise ValueError("all evidence must reference the dataset incident")
        if any(item.incident_id != incident_id for item in self.hypotheses):
            raise ValueError("all hypotheses must reference the dataset incident")
        if self.run.incident_id != incident_id:
            raise ValueError("the run must reference the dataset incident")
        if any(item.incident_id != incident_id for item in self.audit):
            raise ValueError("all audit records must reference the dataset incident")

        for evidence_item in self.evidence:
            _require_known_ids(
                "evidence telemetry",
                evidence_item.telemetry_ids,
                telemetry_ids,
            )
        for hypothesis_item in self.hypotheses:
            _require_known_ids(
                "hypothesis evidence",
                hypothesis_item.evidence_ids,
                evidence_ids,
            )
        _require_known_ids("run evidence", self.run.evidence_ids, evidence_ids)
        _require_known_ids("run hypotheses", self.run.hypothesis_ids, hypothesis_ids)

        valid_targets = {
            "incident": {incident_id},
            "run": {self.run.id},
            "evidence": evidence_ids,
            "hypothesis": hypothesis_ids,
        }
        for audit_item in self.audit:
            if audit_item.run_id != self.run.id:
                raise ValueError("all audit records must reference the dataset run")
            if audit_item.target_id not in valid_targets[audit_item.target_type]:
                raise ValueError(f"audit record references unknown {audit_item.target_type}")
        return self


def _unique_ids(label: str, values: Iterable[str]) -> set[str]:
    """Return a set of IDs and reject duplicates."""

    ids = list(values)
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} IDs must be unique")
    return set(ids)


def _require_known_ids(label: str, values: tuple[str, ...], known: set[str]) -> None:
    """Reject references that are absent from the dataset."""

    unknown = set(values) - known
    if unknown:
        raise ValueError(f"{label} contains unknown IDs: {sorted(unknown)}")
