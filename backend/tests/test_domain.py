"""Tests for incident contracts and the deterministic golden dataset."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from sentinel_api.domain import (
    AuditRecord,
    Evidence,
    GoldenIncidentDataset,
    Hypothesis,
    Incident,
    InvestigationRun,
)
from sentinel_api.fixtures import (
    GOLDEN_SEED,
    build_golden_incident,
    load_golden_incident,
    serialize_golden_incident,
)


def test_all_domain_schemas_validate_the_golden_incident() -> None:
    dataset = build_golden_incident()

    assert Incident.model_validate(dataset.incident.model_dump()) == dataset.incident
    assert Evidence.model_validate(dataset.evidence[0].model_dump()) == dataset.evidence[0]
    assert Hypothesis.model_validate(dataset.hypotheses[0].model_dump()) == dataset.hypotheses[0]
    assert InvestigationRun.model_validate(dataset.run.model_dump()) == dataset.run
    assert AuditRecord.model_validate(dataset.audit[0].model_dump()) == dataset.audit[0]
    assert GoldenIncidentDataset.model_validate_json(serialize_golden_incident()) == dataset


def test_golden_dataset_is_reproducible_from_a_fixed_seed() -> None:
    first = build_golden_incident(GOLDEN_SEED)
    second = build_golden_incident(GOLDEN_SEED)
    different_seed = build_golden_incident(GOLDEN_SEED + 1)

    assert first == second
    assert serialize_golden_incident(GOLDEN_SEED) == serialize_golden_incident(GOLDEN_SEED)
    assert first.incident.id != different_seed.incident.id


def test_serialized_golden_incident_matches_the_generator() -> None:
    fixture_path = (
        Path(__file__).parents[1] / "src" / "sentinel_api" / "data" / "golden_incident.json"
    )

    assert fixture_path.read_text(encoding="utf-8") == serialize_golden_incident()
    assert load_golden_incident() == build_golden_incident()


def test_every_telemetry_item_has_source_and_timestamp_provenance() -> None:
    dataset = build_golden_incident()

    for item in dataset.telemetry:
        assert item.source.system
        assert item.source.locator
        assert item.observed_at.tzinfo is not None


@pytest.mark.parametrize("field", ["source", "observed_at"])
def test_missing_telemetry_provenance_is_rejected(field: str) -> None:
    payload = build_golden_incident().model_dump(mode="json")
    del payload["telemetry"][0][field]

    with pytest.raises(ValidationError, match=field):
        GoldenIncidentDataset.model_validate(payload)


def test_dangling_evidence_reference_is_rejected() -> None:
    payload = build_golden_incident().model_dump(mode="json")
    payload["evidence"][0]["telemetry_ids"] = ["tel_0000000000000000"]

    with pytest.raises(ValidationError, match="unknown IDs"):
        GoldenIncidentDataset.model_validate(payload)
