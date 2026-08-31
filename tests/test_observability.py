# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — diagnostic and clock semantics tests

"""Every branch of the diagnostic plan model and its parsers.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from scpn_mirror_core.errors import DiagnosticPlanError
from scpn_mirror_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    OBSERVABILITY_CATALOGUE_DIGEST,
    OBSERVABILITY_CATALOGUE_VERSION,
    CandidateProfile,
    ClockKind,
    ClockModel,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    ObservabilityBinding,
    ObservabilityClass,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)

DIRECT_BINDINGS = {
    "calibration": "synthetic phase-detector transfer function",
    "clock_epoch": "clk_facility",
    "diagnostic_reference": "synthetic facility drive reference line",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "uncertainty": "declared phase bounds",
    "validity": "synthetic validity window",
}
DERIVED_BINDINGS = {
    "calibration": "synthetic probe transfer functions",
    "clock_epoch": "clk_facility",
    "mode_identity": "declared instability mode labels",
    "observability_threshold": "declared amplitude floor",
    "observation_operator": "synthetic probe-array projection operator",
    "operator_validation": "operator exercised on synthetic fields",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "reference_signal": "synthetic reference oscillator",
    "uncertainty": "declared amplitude and phase bounds",
    "validity": "synthetic validity window",
}
NONCYCLIC_BINDINGS = {
    "calibration": "synthetic calibration set",
    "clock_epoch": "clk_shot",
    "coordinate_frame": "declared axial mirror coordinates",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "uncertainty": "declared bounds",
    "units": "SI units declared per field",
    "validity": "synthetic validity window",
}
NUMERICAL_BINDINGS = {
    "initial_condition": "synthetic initial state",
    "model_revision": "model revision identifier",
    "provenance": "synthetic fixture",
    "simulation_clock": "clk_sim",
    "solver_validity": "declared solver validity envelope",
}


def clock_facility() -> ClockModel:
    """Build the synthetic facility master clock."""
    return ClockModel(
        identifier="clk_facility",
        kind=ClockKind.FACILITY_MONOTONIC,
        epoch="facility master oscillator zero",
        resolution_s=1.0e-9,
        uncertainty_s=5.0e-10,
    )


def clock_shot() -> ClockModel:
    """Build the synthetic shot-epoch clock."""
    return ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="plasma build-up trigger t0",
        resolution_s=1.0e-6,
        uncertainty_s=1.0e-6,
    )


def clock_simulation() -> ClockModel:
    """Build the synthetic simulation clock."""
    return ClockModel(
        identifier="clk_sim",
        kind=ClockKind.SIMULATION,
        epoch="solver step zero",
        resolution_s=1.0e-9,
        uncertainty_s=0.0,
    )


def channel_diamagnetic() -> DiagnosticChannelPlan:
    """Build the synthetic diamagnetic-loop channel."""
    return DiagnosticChannelPlan(
        identifier="ch_diamagnetic_loop",
        candidate_id="open.equilibrium_and_loss",
        carrier=SemanticCarrier.BOUNDED_FEATURE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e5,
        max_signal_frequency_hz=0.0,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        synthetic=True,
    )


def channel_drive_reference() -> DiagnosticChannelPlan:
    """Build the synthetic RF drive-reference channel."""
    return DiagnosticChannelPlan(
        identifier="ch_drive_reference",
        candidate_id="open.drive_reference",
        carrier=SemanticCarrier.CYCLIC_PHASE,
        clock_identifier="clk_facility",
        sample_rate_hz=2.0e8,
        max_signal_frequency_hz=5.0e7,
        evidence_bindings=dict(DIRECT_BINDINGS),
        synthetic=True,
    )


def channel_end_loss() -> DiagnosticChannelPlan:
    """Build the synthetic end-loss analyser channel."""
    return DiagnosticChannelPlan(
        identifier="ch_end_loss_array",
        candidate_id="open.equilibrium_and_loss",
        carrier=SemanticCarrier.BOUNDED_FEATURE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e5,
        max_signal_frequency_hz=0.0,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        synthetic=True,
    )


def channel_flute_probes() -> DiagnosticChannelPlan:
    """Build the synthetic flute-mode probe-array channel."""
    return DiagnosticChannelPlan(
        identifier="ch_flute_probe_array",
        candidate_id="open.resolved_interchange_mode",
        carrier=SemanticCarrier.COMPLEX_MODE,
        clock_identifier="clk_facility",
        sample_rate_hz=1.0e6,
        max_signal_frequency_hz=1.0e4,
        evidence_bindings=dict(DERIVED_BINDINGS),
        synthetic=True,
    )


def channel_oscillator() -> DiagnosticChannelPlan:
    """Build the synthetic model-oscillator channel."""
    return DiagnosticChannelPlan(
        identifier="ch_synthetic_oscillator",
        candidate_id="model.synthetic_oscillator_coordinate",
        carrier=SemanticCarrier.NUMERICAL_PHASE,
        clock_identifier="clk_sim",
        sample_rate_hz=1.0e4,
        max_signal_frequency_hz=0.0,
        evidence_bindings=dict(NUMERICAL_BINDINGS),
        synthetic=True,
    )


def synthetic_plan() -> DiagnosticPlan:
    """Build a fully valid synthetic diagnostic plan."""
    return DiagnosticPlan(
        identifier="mirror_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_end_loss(),
            channel_flute_probes(),
            channel_oscillator(),
        ),
        deferrals=(),
    )


def test_embedded_catalogue_subset_is_exact() -> None:
    """The embedded subset lists exactly the applicable candidates."""
    identifiers = [candidate.candidate_id for candidate in APPLICABLE_CANDIDATES]
    assert identifiers == [
        "model.synthetic_oscillator_coordinate",
        "open.drive_reference",
        "open.equilibrium_and_loss",
        "open.resolved_interchange_mode",
    ]
    assert CATALOGUE_BINDING.catalogue_version == OBSERVABILITY_CATALOGUE_VERSION
    assert CATALOGUE_BINDING.catalogue_digest_sha256 == OBSERVABILITY_CATALOGUE_DIGEST


def test_candidate_properties_follow_class_tables() -> None:
    """Carriers and evidence vocabularies are fixed by the class."""
    by_id = {candidate.candidate_id: candidate for candidate in APPLICABLE_CANDIDATES}
    drive = by_id["open.drive_reference"]
    assert SemanticCarrier.CYCLIC_PHASE in drive.admissible_carriers
    assert "diagnostic_reference" in drive.required_evidence
    interchange = by_id["open.resolved_interchange_mode"]
    assert SemanticCarrier.COMPLEX_MODE in interchange.admissible_carriers
    assert "observation_operator" in interchange.required_evidence
    numerical = by_id["model.synthetic_oscillator_coordinate"]
    assert numerical.admissible_carriers == {SemanticCarrier.NUMERICAL_PHASE}
    assert "simulation_clock" in numerical.required_evidence


def test_binding_rejects_empty_catalogue_version() -> None:
    """An empty catalogue version is rejected."""
    with pytest.raises(DiagnosticPlanError, match="catalogue_version"):
        ObservabilityBinding(
            catalogue_version="",
            catalogue_digest_sha256="0" * 64,
            reactor_registry_version="1.0.0",
            reactor_registry_digest_sha256="0" * 64,
        )


def test_binding_rejects_empty_registry_version() -> None:
    """An empty reactor registry version is rejected."""
    with pytest.raises(DiagnosticPlanError, match="reactor_registry_version"):
        ObservabilityBinding(
            catalogue_version="1.0.0",
            catalogue_digest_sha256="0" * 64,
            reactor_registry_version="",
            reactor_registry_digest_sha256="0" * 64,
        )


@pytest.mark.parametrize(
    ("catalogue_digest", "registry_digest"),
    [("XYZ", "0" * 64), ("0" * 64, "abc")],
)
def test_binding_rejects_malformed_digests(
    catalogue_digest: str, registry_digest: str
) -> None:
    """Digests must be 64 lowercase hexadecimal characters."""
    with pytest.raises(DiagnosticPlanError, match="digest_sha256"):
        ObservabilityBinding(
            catalogue_version="1.0.0",
            catalogue_digest_sha256=catalogue_digest,
            reactor_registry_version="1.0.0",
            reactor_registry_digest_sha256=registry_digest,
        )


def test_candidate_rejects_malformed_identifier() -> None:
    """A malformed candidate identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match="candidate_id"):
        CandidateProfile(
            candidate_id="Bad-Id",
            phenomenon="x",
            configurations=("tandem_mirror",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_empty_phenomenon() -> None:
    """An empty phenomenon statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="phenomenon"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="",
            configurations=("tandem_mirror",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_empty_configurations() -> None:
    """A candidate without configurations is rejected."""
    with pytest.raises(DiagnosticPlanError, match="configurations"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=(),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_unsorted_configurations() -> None:
    """Unsorted or duplicated configurations are rejected."""
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=("tandem_mirror", "gas_dynamic_mirror"),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_foreign_configuration() -> None:
    """A configuration owned by another repository is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not owned"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=("cusp",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_clock_rejects_malformed_identifier() -> None:
    """A malformed clock identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"clock\.identifier"):
        ClockModel(
            identifier="Clock!",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


def test_clock_rejects_empty_epoch() -> None:
    """An empty epoch statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="epoch"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("resolution", [0.0, -1.0, float("nan"), float("inf")])
def test_clock_rejects_bad_resolution(resolution: float) -> None:
    """Non-positive or non-finite resolutions are rejected."""
    with pytest.raises(DiagnosticPlanError, match="resolution_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=resolution,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("uncertainty", [-1.0e-9, float("nan")])
def test_clock_rejects_bad_uncertainty(uncertainty: float) -> None:
    """Negative or non-finite uncertainties are rejected."""
    with pytest.raises(DiagnosticPlanError, match="uncertainty_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=uncertainty,
        )


def _derived(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the derived-cyclic channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_flute_probe_array",
        "candidate_id": "open.resolved_interchange_mode",
        "carrier": SemanticCarrier.COMPLEX_MODE,
        "clock_identifier": "clk_facility",
        "sample_rate_hz": 1.0e6,
        "max_signal_frequency_hz": 1.0e4,
        "evidence_bindings": dict(DERIVED_BINDINGS),
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def test_channel_rejects_malformed_identifier() -> None:
    """A malformed channel identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"channel\.identifier"):
        _derived(identifier="Channel!")


def test_channel_rejects_unknown_candidate() -> None:
    """A candidate outside the embedded subset is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not applicable"):
        _derived(candidate_id="closed.resolved_mhd_mode")


def test_channel_rejects_inadmissible_carrier() -> None:
    """A carrier outside the class table is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not admissible"):
        _derived(carrier=SemanticCarrier.BOUNDED_FEATURE)


def test_channel_rejects_malformed_clock_identifier() -> None:
    """A malformed clock reference is rejected."""
    with pytest.raises(DiagnosticPlanError, match="clock_identifier"):
        _derived(clock_identifier="Clock!")


@pytest.mark.parametrize("rate", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_sample_rate(rate: float) -> None:
    """Non-positive or non-finite sampling rates are rejected."""
    with pytest.raises(DiagnosticPlanError, match="sample_rate_hz"):
        _derived(sample_rate_hz=rate)


@pytest.mark.parametrize("frequency", [-1.0, float("inf")])
def test_channel_rejects_bad_signal_frequency(frequency: float) -> None:
    """Negative or non-finite signal frequencies are rejected."""
    with pytest.raises(DiagnosticPlanError, match="max_signal_frequency_hz"):
        _derived(max_signal_frequency_hz=frequency)


def test_channel_rejects_cyclic_zero_band() -> None:
    """A cyclic channel must declare a positive signal band."""
    with pytest.raises(DiagnosticPlanError, match="positive signal band"):
        _derived(max_signal_frequency_hz=0.0)


def test_direct_channel_rejects_cyclic_zero_band() -> None:
    """A direct-cyclic channel must declare a positive signal band."""
    with pytest.raises(DiagnosticPlanError, match="positive signal band"):
        DiagnosticChannelPlan(
            identifier="ch_drive_reference",
            candidate_id="open.drive_reference",
            carrier=SemanticCarrier.CYCLIC_PHASE,
            clock_identifier="clk_facility",
            sample_rate_hz=2.0e8,
            max_signal_frequency_hz=0.0,
            evidence_bindings=dict(DIRECT_BINDINGS),
            synthetic=True,
        )


def test_channel_rejects_nyquist_violation() -> None:
    """Sampling below twice the signal band is rejected."""
    with pytest.raises(DiagnosticPlanError, match="Nyquist"):
        _derived(sample_rate_hz=1.0e4)


def test_channel_rejects_evidence_key_mismatch() -> None:
    """Missing and extra evidence slots are both rejected."""
    bindings = dict(DERIVED_BINDINGS)
    del bindings["mode_identity"]
    bindings["surprise"] = "x"
    with pytest.raises(DiagnosticPlanError, match=r"missing=.*extra="):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_empty_evidence_statement() -> None:
    """An empty evidence statement is rejected."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["quality"] = ""
    with pytest.raises(DiagnosticPlanError, match="quality"):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_clock_binding_mismatch() -> None:
    """The clock evidence slot must reference the bound clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_other"
    with pytest.raises(DiagnosticPlanError, match="must reference the bound clock"):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_non_synthetic() -> None:
    """No channel in this repository may claim to be real."""
    with pytest.raises(DiagnosticPlanError, match="synthetic"):
        _derived(synthetic=False)


def test_channel_exposes_observability_class() -> None:
    """The class property resolves through the embedded catalogue."""
    assert (
        channel_drive_reference().observability_class
        is ObservabilityClass.DIRECT_CYCLIC
    )
    assert channel_flute_probes().observability_class is (
        ObservabilityClass.DERIVED_CYCLIC
    )


def test_deferral_rejects_unknown_candidate() -> None:
    """A deferral must name an applicable candidate."""
    with pytest.raises(DiagnosticPlanError, match=r"not.*applicable"):
        DeferredCandidate(candidate_id="closed.resolved_mhd_mode", reason="x")


def test_deferral_rejects_empty_reason() -> None:
    """A deferral must carry a reason."""
    with pytest.raises(DiagnosticPlanError, match="reason"):
        DeferredCandidate(
            candidate_id="model.synthetic_oscillator_coordinate", reason=""
        )


def test_plan_accepts_reference_fixture() -> None:
    """The reference plan validates and reports no findings."""
    plan = synthetic_plan()
    assert plan.consistency_report() == ()


def test_plan_accepts_explicit_deferral() -> None:
    """A deferred candidate satisfies the coverage rule."""
    plan = DiagnosticPlan(
        identifier="mirror_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot()),
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_end_loss(),
            channel_flute_probes(),
        ),
        deferrals=(
            DeferredCandidate(
                candidate_id="model.synthetic_oscillator_coordinate",
                reason="synthetic oscillator adds no exercised content here",
            ),
        ),
    )
    assert plan.deferrals[0].candidate_id == ("model.synthetic_oscillator_coordinate")


def test_plan_rejects_malformed_identifier() -> None:
    """A malformed plan identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.identifier"):
        DiagnosticPlan(
            identifier="Plan!",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_foreign_binding() -> None:
    """A binding to any other catalogue release is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.binding"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=ObservabilityBinding(
                catalogue_version="9.9.9",
                catalogue_digest_sha256="0" * 64,
                reactor_registry_version="1.0.0",
                reactor_registry_digest_sha256="0" * 64,
            ),
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_unsorted_clocks() -> None:
    """Clocks must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.clocks"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_shot(), clock_facility(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_unsorted_channels() -> None:
    """Channels must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.channels"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_drive_reference(),
                channel_diamagnetic(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_duplicate_deferrals() -> None:
    """Deferrals must be unique and sorted by candidate identifier."""
    deferral = DeferredCandidate(
        candidate_id="model.synthetic_oscillator_coordinate",
        reason="synthetic oscillator adds no exercised content here",
    )
    with pytest.raises(DiagnosticPlanError, match=r"plan\.deferrals"):
        DiagnosticPlan(
            identifier="mirror_partial_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
            ),
            deferrals=(deferral, deferral),
        )


def test_plan_rejects_undeclared_clock() -> None:
    """A channel bound to an undeclared clock is rejected."""
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_incompatible_clock_kind() -> None:
    """A cyclic channel cannot bind to a shot-epoch clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_shot"
    channel = _derived(clock_identifier="clk_shot", evidence_bindings=bindings)
    with pytest.raises(DiagnosticPlanError, match="incompatible with class"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel,
                channel_oscillator(),
            ),
            deferrals=(),
        )


def test_plan_rejects_planned_and_deferred_overlap() -> None:
    """A candidate cannot be both planned and deferred."""
    with pytest.raises(DiagnosticPlanError, match="both planned and deferred"):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
                channel_oscillator(),
            ),
            deferrals=(
                DeferredCandidate(
                    candidate_id="model.synthetic_oscillator_coordinate",
                    reason="x",
                ),
            ),
        )


def test_plan_rejects_incomplete_coverage() -> None:
    """Every applicable candidate must be planned or deferred."""
    with pytest.raises(DiagnosticPlanError, match="missing="):
        DiagnosticPlan(
            identifier="mirror_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
            ),
            deferrals=(),
        )


def test_report_flags_band_outside_typical_range() -> None:
    """An interchange band above 100 kHz draws the cited advisory."""
    channel = _derived(sample_rate_hz=2.0e7, max_signal_frequency_hz=5.0e6)
    plan = DiagnosticPlan(
        identifier="mirror_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_end_loss(),
            channel,
            channel_oscillator(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "Post 1987" in findings[0].message


def test_report_flags_drive_outside_heating_range() -> None:
    """A drive frequency below 1 MHz draws the cited advisory."""
    channel = DiagnosticChannelPlan(
        identifier="ch_drive_reference",
        candidate_id="open.drive_reference",
        carrier=SemanticCarrier.CYCLIC_PHASE,
        clock_identifier="clk_facility",
        sample_rate_hz=2.0e8,
        max_signal_frequency_hz=1.0e3,
        evidence_bindings=dict(DIRECT_BINDINGS),
        synthetic=True,
    )
    plan = DiagnosticPlan(
        identifier="mirror_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        channels=(
            channel_diamagnetic(),
            channel,
            channel_end_loss(),
            channel_flute_probes(),
            channel_oscillator(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "ICRF" in findings[0].message


def test_report_flags_clock_coarser_than_sampling() -> None:
    """A clock that cannot separate samples draws the advisory."""
    clock = ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="plasma build-up trigger t0",
        resolution_s=1.0e-2,
        uncertainty_s=1.0e-6,
    )
    plan = DiagnosticPlan(
        identifier="mirror_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock, clock_simulation()),
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_flute_probes(),
            channel_oscillator(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "cannot distinguish" in findings[0].message


def test_round_trip_preserves_deferrals() -> None:
    """A plan with an explicit deferral survives the record round-trip."""
    plan = DiagnosticPlan(
        identifier="mirror_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot()),
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_end_loss(),
            channel_flute_probes(),
        ),
        deferrals=(
            DeferredCandidate(
                candidate_id="model.synthetic_oscillator_coordinate",
                reason="synthetic oscillator adds no exercised content here",
            ),
        ),
    )
    assert plan_from_record(plan.to_record()) == plan


def test_round_trip_preserves_digest() -> None:
    """Record and byte round-trips preserve the canonical digest."""
    plan = synthetic_plan()
    rebuilt = plan_from_record(plan.to_record())
    assert rebuilt == plan
    assert plan_from_bytes(plan.canonical_bytes()) == plan
    assert rebuilt.digest_sha256() == plan.digest_sha256()


def test_canonical_bytes_are_sorted_and_terminated() -> None:
    """Canonical bytes use sorted keys and end with a newline."""
    data = synthetic_plan().canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data.decode("utf-8"))
    assert list(decoded) == sorted(decoded)
    digest = hashlib.sha256(data).hexdigest()
    assert synthetic_plan().digest_sha256() == digest


def test_parser_rejects_non_object_record() -> None:
    """A non-object record is rejected."""
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record([1, 2])


def test_parser_rejects_unknown_fields() -> None:
    """Unknown top-level fields are rejected."""
    record = synthetic_plan().to_record()
    record["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown fields"):
        plan_from_record(record)


def test_parser_rejects_non_mapping_binding() -> None:
    """A non-object binding is rejected."""
    record = synthetic_plan().to_record()
    record["binding"] = 3
    with pytest.raises(DiagnosticPlanError, match="binding: must be an object"):
        plan_from_record(record)


@pytest.mark.parametrize("field", ["clocks", "channels", "deferrals"])
def test_parser_rejects_non_list_sections(field: str) -> None:
    """Every plan section must be an array."""
    record = synthetic_plan().to_record()
    record[field] = {}
    with pytest.raises(DiagnosticPlanError, match=f"{field}: must be an array"):
        plan_from_record(record)


@pytest.mark.parametrize("field", ["clocks", "channels", "deferrals"])
def test_parser_rejects_non_object_entries(field: str) -> None:
    """Every section entry must be an object."""
    record = synthetic_plan().to_record()
    record[field] = [1]
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record(record)


def test_parser_rejects_boolean_number() -> None:
    """Booleans are rejected where numbers are required."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["resolution_s"] = True
    with pytest.raises(DiagnosticPlanError, match="must be a number"):
        plan_from_record(record)


def test_parser_accepts_integer_numbers() -> None:
    """Plain integers satisfy numeric fields."""
    record = synthetic_plan().to_record()
    record["channels"][0]["sample_rate_hz"] = 1000
    assert plan_from_record(record).channels[0].sample_rate_hz == 1000.0


def test_parser_rejects_non_boolean_flag() -> None:
    """A non-boolean synthetic flag is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["synthetic"] = "yes"
    with pytest.raises(DiagnosticPlanError, match="must be a boolean"):
        plan_from_record(record)


def test_parser_rejects_non_string_field() -> None:
    """A non-string identifier is rejected."""
    record = synthetic_plan().to_record()
    record["identifier"] = 7
    with pytest.raises(DiagnosticPlanError, match="must be a string"):
        plan_from_record(record)


def test_parser_rejects_unknown_enum_value() -> None:
    """A value outside the enum vocabulary is rejected."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["kind"] = "sundial"
    with pytest.raises(DiagnosticPlanError, match="is not one of"):
        plan_from_record(record)


def test_parser_rejects_non_string_evidence_value() -> None:
    """A non-string evidence statement is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["evidence_bindings"]["provenance"] = 5
    with pytest.raises(DiagnosticPlanError, match="evidence_bindings"):
        plan_from_record(record)


def test_bytes_parser_rejects_nan_literal() -> None:
    """A NaN literal in the document is rejected."""
    record = synthetic_plan().to_record()
    text = json.dumps(record).replace("100000.0", "NaN")
    with pytest.raises(DiagnosticPlanError, match="non-finite"):
        plan_from_bytes(text.encode("utf-8"))


def test_bytes_parser_rejects_invalid_json() -> None:
    """A malformed document is rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"{")


def test_bytes_parser_rejects_invalid_utf8() -> None:
    """Non-UTF-8 bytes are rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"\xff\xfe")
