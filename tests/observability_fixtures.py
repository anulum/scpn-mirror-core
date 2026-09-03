# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — shared diagnostic and clock test fixtures

"""Shared fixtures for the diagnostic plan and clock semantics tests.

The catalogue bindings, signal inventories, clocks, frames, relations and
channel builders used by more than one surface live here so that each test
module states only what is particular to its own surface.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from typing import Any

from scpn_mirror_core.observability import (
    CATALOGUE_BINDING,
    ClockDomain,
    ClockKind,
    ClockModel,
    ClockRelation,
    ClockTopology,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    FrameTransformation,
    ReferenceFrame,
    SemanticCarrier,
    SignalDeclaration,
    SignalRole,
    TransformationKind,
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
    "coordinate_frame": "frm_axial",
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


REFERENCE_FRAMES = (
    ReferenceFrame(
        identifier="frm_axial",
        kind=FrameKind.MACHINE_CYLINDRICAL,
        description="axial mirror cylindrical frame",
    ),
    ReferenceFrame(
        identifier="frm_field_line",
        kind=FrameKind.FIELD_LINE,
        description="field-line following frame between mirror throats",
    ),
)


CLOCK_RELATIONS = (
    ClockRelation(
        child_identifier="clk_shot",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method=(
            "synthetic declaration: trigger timestamped against the "
            "facility oscillator; no correlation evidence claimed"
        ),
        mapping_state="unmapped",
        evidence_claimed=False,
    ),
)


SIGNALS_CH_DIAMAGNETIC_LOOP = (
    SignalDeclaration(
        identifier="sig_diamagnetic_flux",
        quantity="magnetic_flux",
        unit="Wb",
        role=SignalRole.CARRIER,
        description="synthetic diamagnetic flux",
    ),
)


SIGNALS_CH_DRIVE_REFERENCE = (
    SignalDeclaration(
        identifier="sig_drive_frequency",
        quantity="frequency",
        unit="Hz",
        role=SignalRole.AUXILIARY,
        description="declared drive frequency",
    ),
    SignalDeclaration(
        identifier="sig_drive_phase",
        quantity="phase",
        unit="rad",
        role=SignalRole.CARRIER,
        description="synthetic drive reference phase",
    ),
)


SIGNALS_CH_END_LOSS_ARRAY = (
    SignalDeclaration(
        identifier="sig_analyser_energy",
        quantity="energy",
        unit="eV",
        role=SignalRole.AUXILIARY,
        description="declared analyser energy setting",
    ),
    SignalDeclaration(
        identifier="sig_end_loss_flux",
        quantity="particle_flux",
        unit="m^-2/s",
        role=SignalRole.CARRIER,
        description="synthetic end-loss particle flux",
    ),
)


SIGNALS_CH_FLUTE_PROBE_ARRAY = (
    SignalDeclaration(
        identifier="sig_mode_amplitude",
        quantity="magnetic_flux_density",
        unit="T",
        role=SignalRole.AMPLITUDE,
        description="synthetic flute-mode amplitude",
    ),
    SignalDeclaration(
        identifier="sig_mode_number",
        quantity="mode_number",
        unit="1",
        role=SignalRole.AUXILIARY,
        description="declared toroidal or azimuthal mode label",
    ),
    SignalDeclaration(
        identifier="sig_mode_phase",
        quantity="phase",
        unit="rad",
        role=SignalRole.CARRIER,
        description="synthetic mode phase",
    ),
)


SIGNALS_CH_SYNTHETIC_OSCILLATOR = (
    SignalDeclaration(
        identifier="sig_phase",
        quantity="phase",
        unit="rad",
        role=SignalRole.CARRIER,
        description="model-owned synthetic oscillator phase",
    ),
)


REFERENCE_TRANSFORMATIONS: tuple[FrameTransformation, ...] = (
    FrameTransformation(
        source_identifier="frm_axial",
        target_identifier="frm_field_line",
        kind=TransformationKind.FLUX_MAPPING,
        equilibrium_dependent=True,
        method=(
            "synthetic declaration: mapping between the declared frames; "
            "no mapping evidence claimed"
        ),
        evidence_claimed=False,
    ),
)


CLOCK_TOPOLOGY = ClockTopology(
    domains=(
        ClockDomain(
            identifier="dom_facility",
            root_clock_identifier="clk_facility",
            member_clock_identifiers=("clk_facility", "clk_shot"),
            scope="facility master timing and the shot trigger bound to it",
        ),
    ),
    reference_domain_identifier="dom_facility",
)


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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=5.0,
        element_count=1,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        signals=SIGNALS_CH_DIAMAGNETIC_LOOP,
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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=5.0,
        element_count=1,
        evidence_bindings=dict(DIRECT_BINDINGS),
        signals=SIGNALS_CH_DRIVE_REFERENCE,
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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=5.0,
        element_count=8,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        signals=SIGNALS_CH_END_LOSS_ARRAY,
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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=5.0,
        element_count=16,
        evidence_bindings=dict(DERIVED_BINDINGS),
        signals=SIGNALS_CH_FLUTE_PROBE_ARRAY,
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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=1.0,
        element_count=1,
        evidence_bindings=dict(NUMERICAL_BINDINGS),
        signals=SIGNALS_CH_SYNTHETIC_OSCILLATOR,
        synthetic=True,
    )


def synthetic_plan() -> DiagnosticPlan:
    """Build a fully valid synthetic diagnostic plan."""
    return DiagnosticPlan(
        identifier="mirror_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=(
            channel_diamagnetic(),
            channel_drive_reference(),
            channel_end_loss(),
            channel_flute_probes(),
            channel_oscillator(),
        ),
        deferrals=(),
    )


def derived_channel(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the derived-cyclic channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_flute_probe_array",
        "candidate_id": "open.resolved_interchange_mode",
        "carrier": SemanticCarrier.COMPLEX_MODE,
        "clock_identifier": "clk_facility",
        "sample_rate_hz": 1.0e6,
        "max_signal_frequency_hz": 1.0e4,
        "timing_uncertainty_s": None,
        "acquisition_start_s": 0.0,
        "acquisition_duration_s": 5.0,
        "element_count": 16,
        "evidence_bindings": dict(DERIVED_BINDINGS),
        "signals": SIGNALS_CH_FLUTE_PROBE_ARRAY,
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def plan_with(**overrides: Any) -> DiagnosticPlan:
    """Rebuild the synthetic plan with keyword overrides applied."""
    plan = synthetic_plan()
    values: dict[str, Any] = {
        "identifier": plan.identifier,
        "binding": plan.binding,
        "clocks": plan.clocks,
        "frames": plan.frames,
        "clock_relations": plan.clock_relations,
        "frame_transformations": plan.frame_transformations,
        "clock_topology": plan.clock_topology,
        "channels": plan.channels,
        "deferrals": plan.deferrals,
    }
    values.update(overrides)
    return DiagnosticPlan(**values)


def signal_declaration(**overrides: Any) -> SignalDeclaration:
    """Build an auxiliary signal with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "sig_zz_extra",
        "quantity": "current",
        "unit": "A",
        "role": SignalRole.AUXILIARY,
        "description": "synthetic auxiliary signal",
    }
    values.update(overrides)
    return SignalDeclaration(**values)
