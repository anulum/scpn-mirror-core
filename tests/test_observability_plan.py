# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — plan diagnostic tests

"""Whole-plan composition: identity, binding, coverage, deferrals and ordering.

A plan must cover every applicable candidate exactly once, either as a
channel or as an explicit deferral carrying a reason.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import pytest

from observability_fixtures import (
    CLOCK_RELATIONS,
    CLOCK_TOPOLOGY,
    REFERENCE_FRAMES,
    REFERENCE_TRANSFORMATIONS,
    channel_diamagnetic,
    channel_drive_reference,
    channel_end_loss,
    channel_flute_probes,
    channel_oscillator,
    clock_facility,
    clock_shot,
    clock_simulation,
    synthetic_plan,
)
from scpn_mirror_core.errors import DiagnosticPlanError
from scpn_mirror_core.observability import (
    CATALOGUE_BINDING,
    DeferredCandidate,
    DiagnosticPlan,
    ObservabilityBinding,
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
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        frame_transformations=REFERENCE_TRANSFORMATIONS,
        clock_topology=CLOCK_TOPOLOGY,
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
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
            ),
            deferrals=(deferral, deferral),
        )


def test_plan_rejects_planned_and_deferred_overlap() -> None:
    """A candidate cannot be both planned and deferred."""
    with pytest.raises(DiagnosticPlanError, match="both planned and deferred"):
        DiagnosticPlan(
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
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=(
                channel_diamagnetic(),
                channel_drive_reference(),
                channel_end_loss(),
                channel_flute_probes(),
            ),
            deferrals=(),
        )
