# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — frames diagnostic tests

"""Reference frames and the plan rules that keep the frame set connected.

A single-frame plan needs no transformation; a multi-frame plan that
leaves a frame unreachable is refused.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import dataclasses

import pytest

from observability_fixtures import (
    CLOCK_TOPOLOGY,
    REFERENCE_TRANSFORMATIONS,
    plan_with,
    synthetic_plan,
)
from scpn_mirror_core.errors import DiagnosticPlanError
from scpn_mirror_core.observability import (
    DiagnosticPlan,
    FrameKind,
    ReferenceFrame,
)


def test_plan_requires_connected_frames() -> None:
    """With two or more frames, the transformations must connect them all."""
    with pytest.raises(DiagnosticPlanError, match="not connected"):
        plan_with(frame_transformations=())


def test_single_frame_plan_needs_no_transformation() -> None:
    """A single-frame plan carries an empty transformation tuple."""
    plan = synthetic_plan()
    referenced = {
        channel.evidence_bindings.get("coordinate_frame") for channel in plan.channels
    } - {None}
    kept = (
        tuple(frame for frame in plan.frames if frame.identifier in referenced)[:1]
        or plan.frames[:1]
    )
    channels = tuple(
        dataclasses.replace(
            channel,
            evidence_bindings={
                **channel.evidence_bindings,
                **(
                    {"coordinate_frame": kept[0].identifier}
                    if "coordinate_frame" in channel.evidence_bindings
                    else {}
                ),
            },
        )
        for channel in plan.channels
    )
    variant = plan_with(frames=kept, frame_transformations=(), channels=channels)
    assert variant.frame_transformations == ()


def test_frame_rejects_disallowed_kind() -> None:
    """A frame kind outside the repository's allowed set is rejected."""
    with pytest.raises(DiagnosticPlanError, match="allowed frame"):
        ReferenceFrame(
            identifier="frm_bad",
            kind=FrameKind.BOOZER,
            description="x",
        )


def test_frame_rejects_malformed_identifier() -> None:
    """A malformed frame identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"frame\.identifier"):
        ReferenceFrame(
            identifier="Frame!",
            kind=FrameKind.MACHINE_CYLINDRICAL,
            description="x",
        )


def test_frame_rejects_empty_description() -> None:
    """An empty frame description is rejected."""
    with pytest.raises(DiagnosticPlanError, match="description"):
        ReferenceFrame(
            identifier="frm_ok",
            kind=FrameKind.MACHINE_CYLINDRICAL,
            description="",
        )


def test_plan_rejects_duplicate_frames() -> None:
    """Duplicate frame identifiers are rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match=r"plan\.frames"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=(*plan.frames, plan.frames[0]),
            clock_relations=plan.clock_relations,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_rejects_unknown_frame_reference() -> None:
    """A coordinate_frame binding must name a declared frame."""
    plan = synthetic_plan()
    kept = tuple(frame for frame in plan.frames if frame.identifier != "frm_axial")
    with pytest.raises(DiagnosticPlanError, match="declared frame"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=kept,
            clock_relations=plan.clock_relations,
            frame_transformations=REFERENCE_TRANSFORMATIONS,
            clock_topology=CLOCK_TOPOLOGY,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )
