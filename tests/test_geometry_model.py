# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device 3D model tests

"""Body inventory, placement, volumes, clearances and record identity.

The axial stations are recomputed here from the fixture numbers rather
than read back from the model, so a change in the composition shows up as
a failure instead of agreeing with itself. The analytic volumes are the
closed forms of the primitives the library builds — including the exact
frustum-stack volume of the flux tube, which a linear profile makes
exact rather than approximate. All values are synthetic.
"""

from __future__ import annotations

import hashlib
import json
import math

import pytest

from geometry_fixtures import (
    REFERENCE_CELL_LENGTH_M,
    REFERENCE_MIDPLANE_FIELD_T,
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
)
from scpn_mirror_core.geometry import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    aperture_sections,
    axial_stations,
    build_device_model,
)

#: Digest of the reference tier-G1 model record at eight segments.
REFERENCE_MODEL_SHA256 = (
    "16cd38c8f926107f8519c589d7098dbffa4db394e06341f61142d6be2f95ac39"
)

#: Axial stations of the synthetic design, from the fixture numbers alone:
#: throats at half the declared cell length, mirror coils centred on them,
#: the vessel between their inboard faces, a tank on each outboard face and
#: an end wall closing each tank.
VESSEL_END_M = REFERENCE_CELL_LENGTH_M / 2.0 - 0.4 / 2.0
THROAT_M = REFERENCE_CELL_LENGTH_M / 2.0
COIL_END_M = REFERENCE_CELL_LENGTH_M / 2.0 + 0.4 / 2.0
EXPANDER_END_M = COIL_END_M + 1.0
END_WALL_END_M = EXPANDER_END_M + 0.05
TRIM_LOW_M = 0.5 - 0.3 / 2.0
TRIM_HIGH_M = 0.5 + 0.3 / 2.0


def reference_model(segments: int = 16) -> DeviceModel3D:
    """Build the reference model of these tests at a segment count."""
    return build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        segments,
    )


def expected_tube_profile() -> tuple[tuple[float, float], ...]:
    """Return the flux-tube profile from the fixture field profile alone."""
    return tuple(
        (
            height,
            REFERENCE_MIDPLANE_PLASMA_RADIUS_M
            * math.sqrt(REFERENCE_MIDPLANE_FIELD_T / strength),
        )
        for height, strength in reference_field_profile()
    )


def frustum_stack_volume(profile: tuple[tuple[float, float], ...]) -> float:
    """Return the exact volume of the solid of revolution of a linear profile."""
    total = 0.0
    for index in range(len(profile) - 1):
        low_z, low_radius = profile[index]
        high_z, high_radius = profile[index + 1]
        total += (
            (math.pi / 3.0)
            * (low_radius**2 + low_radius * high_radius + high_radius**2)
            * (high_z - low_z)
        )
    return total


def test_bodies_roles_and_materials() -> None:
    """Ten bodies in the fixed order with the declared roles and materials."""
    model = reference_model()
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES
    assert [mesh.role for mesh in model.meshes] == [
        "vacuum_boundary",
        "coil",
        "coil",
        "coil",
        "coil",
        "vacuum_boundary",
        "vacuum_boundary",
        "vacuum_boundary",
        "vacuum_boundary",
        "plasma",
    ]
    assert [mesh.material_identifier for mesh in model.meshes] == [
        "vessel_wall",
        "coil_conductor",
        "coil_conductor",
        "coil_conductor",
        "coil_conductor",
        "vessel_wall",
        "vessel_wall",
        "end_wall",
        "end_wall",
        "plasma",
    ]
    for mesh in model.meshes:
        assert mesh.signed_volume_m3() > 0.0


def test_stations_come_from_the_cell_length_and_nowhere_else() -> None:
    """The throats are half the declared cell length; every station follows."""
    stations = axial_stations(reference_configuration(), reference_geometry())
    assert stations.throat_m == THROAT_M
    assert stations.vessel_end_m == VESSEL_END_M
    assert stations.coil_end_m == COIL_END_M
    assert stations.expander_end_m == EXPANDER_END_M
    assert stations.end_wall_end_m == END_WALL_END_M
    assert stations.central_cell_coil_low_m == TRIM_LOW_M
    assert stations.central_cell_coil_high_m == TRIM_HIGH_M


def test_the_mirror_coils_are_centred_on_the_throats() -> None:
    """Each mirror coil straddles its throat, symmetrically and without gap."""
    geometry = reference_geometry()
    model = reference_model()
    upstream = model.meshes[3].bounding_box()
    downstream = model.meshes[4].bounding_box()
    assert upstream[0][2] == -COIL_END_M
    assert upstream[1][2] == -VESSEL_END_M
    assert downstream[0][2] == VESSEL_END_M
    assert downstream[1][2] == COIL_END_M
    for box in (upstream, downstream):
        centre = (box[0][2] + box[1][2]) / 2.0
        assert abs(centre) == pytest.approx(THROAT_M)
        assert (box[1][2] - box[0][2]) == pytest.approx(geometry.mirror_coil_length_m)
        assert box[1][0] == geometry.mirror_coil_outer_radius_m


def test_the_vessel_spans_between_the_coil_inboard_faces() -> None:
    """The central-cell vessel meets both mirror coils face to face."""
    geometry = reference_geometry()
    vessel = reference_model().meshes[0].bounding_box()
    assert vessel[0][2] == -VESSEL_END_M
    assert vessel[1][2] == VESSEL_END_M
    assert vessel[1][0] == geometry.central_cell_vessel_outer_radius_m


def test_the_central_cell_coils_are_wound_on_the_vessel_inside_the_cell() -> None:
    """Both trim coils sit outside the vessel wall and inside the cell."""
    geometry = reference_geometry()
    model = reference_model()
    upstream = model.meshes[1].bounding_box()
    downstream = model.meshes[2].bounding_box()
    assert upstream[0][2] == -TRIM_HIGH_M
    assert upstream[1][2] == -TRIM_LOW_M
    assert downstream[0][2] == TRIM_LOW_M
    assert downstream[1][2] == TRIM_HIGH_M
    assert downstream[1][2] < VESSEL_END_M
    for box in (upstream, downstream):
        assert box[1][0] == geometry.central_cell_coil_outer_radius_m
    assert (
        geometry.central_cell_coil_bore_radius_m
        >= geometry.central_cell_vessel_outer_radius_m
    )


def test_each_tank_starts_at_its_coil_and_its_end_wall_closes_it() -> None:
    """The tanks and end walls follow the coils face to face at both ends."""
    geometry = reference_geometry()
    model = reference_model()
    tank_up = model.meshes[5].bounding_box()
    tank_down = model.meshes[6].bounding_box()
    wall_up = model.meshes[7].bounding_box()
    wall_down = model.meshes[8].bounding_box()
    assert tank_up[1][2] == -COIL_END_M
    assert tank_up[0][2] == -EXPANDER_END_M
    assert tank_down[0][2] == COIL_END_M
    assert tank_down[1][2] == EXPANDER_END_M
    assert wall_up[1][2] == tank_up[0][2]
    assert wall_down[0][2] == tank_down[1][2]
    assert wall_up[0][2] == -END_WALL_END_M
    assert wall_down[1][2] == END_WALL_END_M
    for box in (tank_up, tank_down, wall_up, wall_down):
        assert box[1][0] == geometry.expander_tank_outer_radius_m


def test_the_flux_tube_is_the_declared_field_under_flux_conservation() -> None:
    """The tenth body is the surface of revolution of the derived profile."""
    model = reference_model()
    expected = expected_tube_profile()
    assert model.tube_profile == expected
    tube = model.meshes[9].bounding_box()
    assert tube[0][2] == expected[0][0]
    assert tube[1][2] == expected[-1][0]
    assert tube[1][0] == max(radius for _, radius in expected)


def test_the_flux_tube_is_not_a_body_of_constant_radius() -> None:
    """The narrowest and widest radii differ by the field variation.

    This is the assertion that separates this family from the five built
    on cylinders: a mirror column cannot be drawn as one radius, because
    the field it sits in is not one strength.
    """
    profile = expected_tube_profile()
    radii = [radius for _, radius in profile]
    assert min(radii) < max(radii)
    field = [strength for _, strength in reference_field_profile()]
    assert min(radii) / max(radii) == pytest.approx(
        math.sqrt(min(field) / max(field)), rel=1.0e-15
    )


def test_volumes_follow_the_analytic_bodies() -> None:
    """Each body volume converges on its analytic closed form from below."""
    geometry = reference_geometry()
    vessel_bore = geometry.central_cell_vessel_bore_radius_m
    vessel_outer = geometry.central_cell_vessel_outer_radius_m
    trim_bore = geometry.central_cell_coil_bore_radius_m
    trim_outer = geometry.central_cell_coil_outer_radius_m
    warm_bore = geometry.mirror_coil_warm_bore_radius_m
    mirror_outer = geometry.mirror_coil_outer_radius_m
    tank_bore = geometry.expander_tank_bore_radius_m
    tank_outer = geometry.expander_tank_outer_radius_m
    analytic = [
        math.pi * (vessel_outer**2 - vessel_bore**2) * (2.0 * VESSEL_END_M),
        math.pi * (trim_outer**2 - trim_bore**2) * (TRIM_HIGH_M - TRIM_LOW_M),
        math.pi * (trim_outer**2 - trim_bore**2) * (TRIM_HIGH_M - TRIM_LOW_M),
        math.pi * (mirror_outer**2 - warm_bore**2) * (COIL_END_M - VESSEL_END_M),
        math.pi * (mirror_outer**2 - warm_bore**2) * (COIL_END_M - VESSEL_END_M),
        math.pi * (tank_outer**2 - tank_bore**2) * (EXPANDER_END_M - COIL_END_M),
        math.pi * (tank_outer**2 - tank_bore**2) * (EXPANDER_END_M - COIL_END_M),
        math.pi * tank_outer**2 * (END_WALL_END_M - EXPANDER_END_M),
        math.pi * tank_outer**2 * (END_WALL_END_M - EXPANDER_END_M),
        frustum_stack_volume(expected_tube_profile()),
    ]
    model = reference_model(1024)
    for mesh, exact in zip(model.meshes, analytic, strict=True):
        assert 0.0 < (exact - mesh.signed_volume_m3()) / exact < 1.0e-5, mesh.name


def test_clearances_cover_every_section_the_tube_enters() -> None:
    """The record states the tube's widest radius per section and its bore."""
    model = reference_model()
    sections = aperture_sections(
        reference_geometry(),
        axial_stations(reference_configuration(), reference_geometry()),
    )
    assert [item.section for item in model.clearances] == [
        section.name for section in sections
    ]
    for item, section in zip(model.clearances, sections, strict=True):
        assert item.bore_radius_m == section.bore_radius_m
        assert item.clearance_m > 0.0
        assert item.largest_flux_tube_radius_m < item.bore_radius_m


def test_the_tube_clears_the_throat_it_has_to_pass() -> None:
    """The narrowest aperture of the assembly is cleared by the column."""
    geometry = reference_geometry()
    model = reference_model()
    throat = [
        item
        for item in model.clearances
        if item.bore_radius_m == geometry.mirror_coil_warm_bore_radius_m
    ]
    assert len(throat) == 2
    for item in throat:
        assert item.largest_flux_tube_radius_m < geometry.mirror_coil_warm_bore_radius_m


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_model(
        configuration,
        geometry,
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        8,
    )
    record = model.to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["units"] == MODEL_UNITS
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["midplane_plasma_radius_m"] == REFERENCE_MIDPLANE_PLASMA_RADIUS_M
    assert record["field_profile"] == [
        list(sample) for sample in reference_field_profile()
    ]
    assert record["flux_tube_profile"] == [
        list(sample) for sample in expected_tube_profile()
    ]
    assert [item["section"] for item in record["flux_tube_clearances"]] == [
        item.section for item in model.clearances
    ]
    assert record["segments"] == 8
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_MODEL_SHA256


def test_model_is_deterministic() -> None:
    """Two builds of the same inputs are equal and share every digest."""
    first = reference_model(32)
    second = reference_model(32)
    assert first == second
    assert first.digest_sha256() == second.digest_sha256()
    assert [mesh.digest_sha256() for mesh in first.meshes] == [
        mesh.digest_sha256() for mesh in second.meshes
    ]


def test_a_different_field_profile_is_a_different_model() -> None:
    """The declared field is part of the model identity, not a hint."""
    finer = (
        *reference_field_profile()[:4],
        (-0.3, 0.7),
        *reference_field_profile()[4:],
    )
    other = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        finer,
        8,
    )
    baseline = reference_model(8)
    assert other.digest_sha256() != baseline.digest_sha256()
    assert other.meshes[9].digest_sha256() != baseline.meshes[9].digest_sha256()
    assert other.meshes[0].digest_sha256() == baseline.meshes[0].digest_sha256()
