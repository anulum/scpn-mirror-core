# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — transformations diagnostic tests

"""Frame transformations and the plan rules that govern them.

Ordering, duplication, undeclared targets and inadmissible kinds are
each refused, as is a transformation that claims evidence it does not carry.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

from typing import Any

import pytest

from observability_fixtures import (
    plan_with,
    synthetic_plan,
)
from scpn_mirror_core.errors import DiagnosticPlanError
from scpn_mirror_core.observability import (
    FrameKind,
    FrameTransformation,
    ReferenceFrame,
    TransformationKind,
)


def _transformation(**overrides: Any) -> FrameTransformation:
    """Build a transformation with keyword overrides applied."""
    values: dict[str, Any] = {
        "source_identifier": "frm_axial",
        "target_identifier": "frm_field_line",
        "kind": TransformationKind.FLUX_MAPPING,
        "equilibrium_dependent": True,
        "method": "synthetic declaration",
        "evidence_claimed": False,
    }
    values.update(overrides)
    return FrameTransformation(**values)


def _extra_frame(identifier: str) -> ReferenceFrame:
    """Build an additional synthetic frame of an allowed kind."""
    return ReferenceFrame(
        identifier=identifier,
        kind=FrameKind.FIELD_LINE,
        description="additional synthetic frame",
    )


@pytest.mark.parametrize("field", ["source_identifier", "target_identifier"])
def test_transformation_rejects_malformed_identifier(field: str) -> None:
    """Malformed frame identifiers are rejected."""
    with pytest.raises(DiagnosticPlanError, match=rf"transformation\.{field}"):
        _transformation(**{field: "Frame!"})


def test_transformation_rejects_self_mapping() -> None:
    """A frame cannot be transformed to itself."""
    with pytest.raises(DiagnosticPlanError, match="to itself"):
        _transformation(target_identifier="frm_axial")


@pytest.mark.parametrize(
    ("kind", "dependent"),
    [
        (TransformationKind.FLUX_MAPPING, False),
        (TransformationKind.RIGID, True),
        (TransformationKind.PROJECTION, True),
    ],
)
def test_transformation_rejects_equilibrium_flag_mismatch(
    kind: TransformationKind, dependent: bool
) -> None:
    """Only flux mappings depend on an equilibrium reconstruction."""
    with pytest.raises(DiagnosticPlanError, match="equilibrium_dependent"):
        _transformation(kind=kind, equilibrium_dependent=dependent)


def test_transformation_rejects_empty_method() -> None:
    """An empty method statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"transformation\.method"):
        _transformation(method="")


def test_transformation_rejects_claimed_evidence() -> None:
    """No mapping evidence may be claimed."""
    with pytest.raises(DiagnosticPlanError, match="evidence_claimed"):
        _transformation(evidence_claimed=True)


def test_plan_rejects_unsorted_transformations() -> None:
    """Transformations must be sorted by source then target."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="must be sorted"):
        plan_with(
            frames=tuple(
                sorted(
                    (*plan.frames, _extra_frame("frm_zz_extra")),
                    key=lambda frame: frame.identifier,
                )
            ),
            frame_transformations=(
                _transformation(
                    source_identifier="frm_field_line",
                    target_identifier="frm_zz_extra",
                    kind=TransformationKind.FLUX_MAPPING,
                    equilibrium_dependent=True,
                ),
                _transformation(),
            ),
        )


def test_plan_rejects_duplicate_transformation_pair() -> None:
    """At most one transformation per unordered frame pair."""
    with pytest.raises(DiagnosticPlanError, match="duplicate transformation pair"):
        plan_with(
            frame_transformations=(
                _transformation(),
                _transformation(
                    source_identifier="frm_field_line", target_identifier="frm_axial"
                ),
            )
        )


def test_plan_rejects_transformation_to_undeclared_frame() -> None:
    """Transformations reference declared frames only."""
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        plan_with(
            frame_transformations=tuple(
                sorted(
                    (
                        *synthetic_plan().frame_transformations,
                        _transformation(target_identifier="frm_zz_ghost"),
                    ),
                    key=lambda item: (item.source_identifier, item.target_identifier),
                )
            )
        )


def test_plan_rejects_inadmissible_transformation_kind() -> None:
    """The kind must be admissible for the two frame kinds."""
    wrong = _transformation(kind=TransformationKind.RIGID, equilibrium_dependent=False)
    with pytest.raises(DiagnosticPlanError, match="not admissible"):
        plan_with(
            frame_transformations=tuple(
                wrong
                if (item.source_identifier, item.target_identifier)
                == ("frm_axial", "frm_field_line")
                else item
                for item in synthetic_plan().frame_transformations
            )
        )
