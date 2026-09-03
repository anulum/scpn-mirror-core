# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — report diagnostic tests

"""The review report and the ranges it flags.

The report advises; it does not refuse. Each flag names the quantity, the
range it fell outside, and the channel it came from.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    DIRECT_BINDINGS,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    SIGNALS_CH_DRIVE_REFERENCE,
    SIGNALS_CH_FLUTE_PROBE_ARRAY,
    channel_diamagnetic,
    channel_drive_reference,
    channel_end_loss,
    channel_flute_probes,
    channel_oscillator,
    clock_facility,
    clock_shot,
    clock_simulation,
    derived_channel,
    plan_with,
    synthetic_plan,
)
from scpn_mirror_core.observability import (
    CATALOGUE_BINDING,
    ClockKind,
    ClockModel,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    SemanticCarrier,
    SignalRole,
)


def test_report_flags_cyclic_array_without_amplitude_signal() -> None:
    """A multi-element cyclic array without an amplitude signal draws the advisory."""
    channel = derived_channel(
        signals=tuple(
            signal
            for signal in SIGNALS_CH_FLUTE_PROBE_ARRAY
            if signal.role is not SignalRole.AMPLITUDE
        )
    )
    plan = plan_with(
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in synthetic_plan().channels
        )
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "amplitude" in findings[0].message


def test_report_flags_band_outside_typical_range() -> None:
    """An interchange band above 100 kHz draws the cited advisory."""
    channel = derived_channel(sample_rate_hz=2.0e7, max_signal_frequency_hz=5.0e6)
    plan = DiagnosticPlan(
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
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=5.0,
        element_count=1,
        evidence_bindings=dict(DIRECT_BINDINGS),
        signals=SIGNALS_CH_DRIVE_REFERENCE,
        synthetic=True,
    )
    plan = DiagnosticPlan(
        identifier="mirror_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
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
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
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


def test_report_flags_window_beyond_device_ceiling() -> None:
    """An acquisition window beyond the device scale draws the advisory."""
    channel = derived_channel(acquisition_duration_s=100.0)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "acquisition window" in findings[0].message


def test_report_flags_array_size_outside_common_range() -> None:
    """A two-element array below the common range draws the advisory."""
    channel = derived_channel(element_count=2)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "array size" in findings[0].message
