# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — anchor tests against a published arrangement

"""Every dimension the filed source prints, in the built bodies.

The anchor fixtures carry the values printed in sections 2 and 2.1 of the
WHAM physics basis already on file (D. Endrizzi et al., J. Plasma Phys.
89 (2023) 975890501, CC BY 4.0): a target plasma of radius ``a = 0.1 m``;
``17 T``, ``5.5 cm`` warm bore HTS mirror magnets centred at
``z = +-98 cm``; two coils near the midplane at ``z = +-20 cm`` raising
the central field to a maximum of ``0.86 T``. These tests prove the tier
can carry that arrangement — that each printed number appears in the
bodies the model builds, and that the column narrows *through* the
printed bore rather than intersecting it.

Reproducing a printed dimension is an anchor, never a claim about that
machine. Everything the source does not print is declared in the fixture
and marked as declared, the axial field profile between the printed
endpoints included.
"""

from __future__ import annotations

import math

import pytest

from geometry_fixtures import (
    ANCHOR_CENTRAL_CELL_COIL_OFFSET_M,
    ANCHOR_MIDPLANE_FIELD_T,
    ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
    ANCHOR_THROAT_FIELD_T,
    ANCHOR_THROAT_POSITION_M,
    ANCHOR_WARM_BORE_RADIUS_M,
    anchor_configuration,
    anchor_field_profile,
    anchor_geometry,
    coarse_anchor_field_profile,
)
from scpn_mirror_core.geometry import (
    BODY_NAMES,
    DeviceModel3D,
    build_device_model,
)


def anchor_model(segments: int = 64) -> DeviceModel3D:
    """Build the anchor model at a segment count."""
    return build_device_model(
        anchor_configuration(),
        anchor_geometry(),
        ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
        anchor_field_profile(),
        segments,
    )


def coarse_anchor_model(segments: int = 64) -> DeviceModel3D:
    """Build the anchor model from the printed endpoints alone."""
    return build_device_model(
        anchor_configuration(),
        anchor_geometry(),
        ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
        coarse_anchor_field_profile(),
        segments,
    )


def test_the_printed_magnet_positions_are_the_coil_centres() -> None:
    """Both mirror coils are centred on the printed ``z = +-98 cm``."""
    model = anchor_model()
    upstream = model.meshes[3].bounding_box()
    downstream = model.meshes[4].bounding_box()
    for box, sign in ((upstream, -1.0), (downstream, 1.0)):
        centre = (box[0][2] + box[1][2]) / 2.0
        assert centre == pytest.approx(sign * ANCHOR_THROAT_POSITION_M, abs=1.0e-12)
    assert anchor_configuration().layout.central_cell_length_m == (
        2.0 * ANCHOR_THROAT_POSITION_M
    )


def test_the_printed_warm_bore_is_the_mirror_coil_bore() -> None:
    """The coil bore is the printed 5.5 cm aperture, as a radius."""
    geometry = anchor_geometry()
    assert geometry.mirror_coil_warm_bore_radius_m == ANCHOR_WARM_BORE_RADIUS_M
    assert 2.0 * geometry.mirror_coil_warm_bore_radius_m == pytest.approx(0.055)
    coil = anchor_model().meshes[4]
    assert coil.bounding_box()[1][0] == pytest.approx(
        geometry.mirror_coil_outer_radius_m
    )


def test_the_printed_midplane_coil_offset_is_a_body_position() -> None:
    """The pair printed at ``z = +-20 cm`` are bodies, not a footnote."""
    model = anchor_model()
    upstream = model.meshes[1].bounding_box()
    downstream = model.meshes[2].bounding_box()
    for box, sign in ((upstream, -1.0), (downstream, 1.0)):
        centre = (box[0][2] + box[1][2]) / 2.0
        assert centre == pytest.approx(
            sign * ANCHOR_CENTRAL_CELL_COIL_OFFSET_M, abs=1.0e-12
        )


def test_the_printed_fields_are_the_declared_profile_endpoints() -> None:
    """The midplane and throat samples are the printed field strengths."""
    profile = anchor_field_profile()
    midplane = next(strength for height, strength in profile if height == 0.0)
    assert midplane == ANCHOR_MIDPLANE_FIELD_T
    assert max(strength for _, strength in profile) == ANCHOR_THROAT_FIELD_T
    for height, strength in profile:
        if abs(height) == ANCHOR_THROAT_POSITION_M:
            assert strength == ANCHOR_THROAT_FIELD_T


def test_the_printed_plasma_radius_is_the_midplane_radius_of_the_column() -> None:
    """The column is the printed ``a = 0.1 m`` where the source prints it."""
    model = anchor_model()
    midplane = next(radius for height, radius in model.tube_profile if height == 0.0)
    assert midplane == ANCHOR_MIDPLANE_PLASMA_RADIUS_M
    assert model.meshes[9].bounding_box()[1][0] == pytest.approx(
        ANCHOR_MIDPLANE_PLASMA_RADIUS_M, rel=1.0e-3
    )


def test_a_cylinder_of_the_printed_radius_does_not_pass_the_printed_bore() -> None:
    """The arithmetic that forced this family, stated as an assertion.

    The source prints a plasma radius of 0.1 m and a magnet aperture of
    5.5 cm. A body of constant radius 0.1 m cannot exist inside a bore of
    radius 0.0275 m, so the column is not a cylinder — not as a modelling
    preference, but because two printed numbers do not close under that
    shape.
    """
    assert ANCHOR_MIDPLANE_PLASMA_RADIUS_M > ANCHOR_WARM_BORE_RADIUS_M


def test_the_column_narrows_through_the_printed_bore() -> None:
    """The flux tube clears the printed aperture, and by how much is recorded."""
    model = anchor_model()
    ratio = anchor_configuration().field.mirror_ratio
    throat_radius = ANCHOR_MIDPLANE_PLASMA_RADIUS_M / math.sqrt(ratio)
    assert throat_radius < ANCHOR_WARM_BORE_RADIUS_M
    narrowest = min(radius for _, radius in model.tube_profile)
    assert narrowest == pytest.approx(throat_radius, rel=1.0e-15)
    throat_sections = [
        item
        for item in model.clearances
        if item.bore_radius_m == ANCHOR_WARM_BORE_RADIUS_M
    ]
    assert len(throat_sections) == 2
    for item in throat_sections:
        assert item.clearance_m > 0.0
        assert item.largest_flux_tube_radius_m < ANCHOR_WARM_BORE_RADIUS_M
        assert item.largest_flux_tube_radius_m >= narrowest


def test_the_column_is_widest_at_the_midplane_and_narrowest_at_the_throats() -> None:
    """The declared profile puts the extremes where the field puts them."""
    model = anchor_model()
    widest = max(model.tube_profile, key=lambda sample: sample[1])
    narrowest = min(model.tube_profile, key=lambda sample: sample[1])
    assert widest[0] == 0.0
    assert abs(narrowest[0]) == ANCHOR_THROAT_POSITION_M


def test_the_anchor_bodies_are_the_family_inventory() -> None:
    """The anchor is a parameter set, not a different model."""
    model = anchor_model(8)
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES
    for mesh in model.meshes:
        assert mesh.signed_volume_m3() > 0.0


def test_the_coarse_profile_is_a_different_body_and_not_a_safe_one() -> None:
    """Dropping the declared samples changes the column, in both directions.

    The linear-between-samples contract is exact, not conservative: with
    only the printed endpoints the straight line between the midplane
    radius and the throat radius runs *inside* the finer column near the
    throat, so the coarse profile reports a larger clearance than the
    finer one. A reader must not treat the coarse record as a bound on
    the finer one, and the digests say they are different bodies.
    """
    fine = anchor_model(8)
    coarse = coarse_anchor_model(8)
    assert fine.digest_sha256() != coarse.digest_sha256()
    assert fine.meshes[9].digest_sha256() != coarse.meshes[9].digest_sha256()
    fine_throat = next(
        item.largest_flux_tube_radius_m
        for item in fine.clearances
        if item.bore_radius_m == ANCHOR_WARM_BORE_RADIUS_M
    )
    coarse_throat = next(
        item.largest_flux_tube_radius_m
        for item in coarse.clearances
        if item.bore_radius_m == ANCHOR_WARM_BORE_RADIUS_M
    )
    assert coarse_throat < fine_throat
    for model in (fine, coarse):
        assert min(radius for _, radius in model.tube_profile) == pytest.approx(
            ANCHOR_MIDPLANE_PLASMA_RADIUS_M
            / math.sqrt(anchor_configuration().field.mirror_ratio),
            rel=1.0e-15,
        )
