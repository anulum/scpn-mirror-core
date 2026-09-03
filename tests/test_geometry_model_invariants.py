# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device 3D model build-invariant tests

"""The fail-closed gate of the model build, one refusal at a time.

The model tests cover the product; this file covers the gate. Each case
violates exactly one invariant and asserts the refusal names the field or
the section responsible, so a caller can act on the message rather than
guess. Every aperture refusal is placed so that only the section under
test is violated and the sections checked before it still clear. All
values are synthetic.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from geometry_fixtures import (
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
)
from scpn_mirror_core.configuration import DeviceConfiguration
from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.geometry import (
    DeviceGeometry,
    DeviceModel3D,
    FieldProfile,
    build_device_model,
)
from scpn_mirror_core.parameters import CellLayout, MirrorField


def build(
    configuration: DeviceConfiguration | None = None,
    geometry: DeviceGeometry | None = None,
    radius: float | None = None,
    profile: FieldProfile | None = None,
    segments: int = 8,
) -> DeviceModel3D:
    """Build the reference model with the named parts replaced.

    Every parameter is typed rather than collected into a mapping, so the
    helper needs no type-checker suppression: a suppression here would
    hide exactly the argument mistakes these tests exist to catch.

    Parameters
    ----------
    configuration, geometry, radius, profile, segments
        Replacements for the reference design; ``None`` keeps the
        reference part.

    Returns
    -------
    DeviceModel3D
        The built model, when the overridden design is accepted.
    """
    return build_device_model(
        reference_configuration() if configuration is None else configuration,
        reference_geometry() if geometry is None else geometry,
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M if radius is None else radius,
        reference_field_profile() if profile is None else profile,
        segments,
    )


@pytest.mark.parametrize("segments", [0, 4, 20, 7])
def test_the_segment_rule_is_checked_first(segments: int) -> None:
    """An invalid segment count is refused before anything is built."""
    with pytest.raises(DeviceGeometryError):
        build(segments=segments)


@pytest.mark.parametrize("radius", [0.0, -0.001, math.nan, math.inf])
def test_the_midplane_radius_must_be_finite_and_positive(radius: float) -> None:
    """A non-finite or non-positive column radius fails closed."""
    with pytest.raises(DeviceGeometryError, match="midplane_plasma_radius_m"):
        build(radius=radius)


def test_a_cell_no_longer_than_a_mirror_coil_is_refused() -> None:
    """The vessel spans between the coils, so the cell has to be longer."""
    configuration = dataclasses.replace(
        reference_configuration(),
        layout=CellLayout(central_cell_length_m=0.4, end_plug_cell_count=0),
    )
    with pytest.raises(DeviceGeometryError, match="central_cell_length_m"):
        build(configuration=configuration)


def test_central_cell_coils_that_would_cross_the_midplane_are_refused() -> None:
    """Two coils at an offset under half their length would intersect."""
    geometry = dataclasses.replace(reference_geometry(), central_cell_coil_offset_m=0.1)
    with pytest.raises(DeviceGeometryError, match="central_cell_coil_offset_m"):
        build(geometry=geometry)


def test_a_central_cell_coil_outside_the_cell_is_refused() -> None:
    """A trim coil past the vessel end would sit on the mirror coil."""
    geometry = dataclasses.replace(
        reference_geometry(), central_cell_coil_offset_m=0.95
    )
    with pytest.raises(DeviceGeometryError, match="central_cell_coil_offset_m"):
        build(geometry=geometry)


def test_the_field_profile_contract_is_enforced_by_the_build() -> None:
    """A profile the contract refuses never reaches the composition."""
    with pytest.raises(DeviceGeometryError, match="at least 2 samples"):
        build(profile=((0.0, 0.5),))


def test_a_profile_without_a_midplane_sample_is_refused_by_the_build() -> None:
    """The build needs the field at the plane the declared radius belongs to."""
    profile = tuple(sample for sample in reference_field_profile() if sample[0] != 0.0)
    with pytest.raises(DeviceGeometryError, match=r"sample at z = 0\.0"):
        build(profile=profile)


def test_a_midplane_field_that_contradicts_the_configuration_is_refused() -> None:
    """The declared profile has to agree with the configuration's b_min_t."""
    profile = tuple(
        (height, 0.6 if height == 0.0 else strength)
        for height, strength in reference_field_profile()
    )
    with pytest.raises(DeviceGeometryError, match="b_min_t"):
        build(profile=profile)


def test_a_throat_field_that_contradicts_the_configuration_is_refused() -> None:
    """The largest declared sample has to be the configuration's b_max_t."""
    configuration = dataclasses.replace(
        reference_configuration(), field=MirrorField(b_max_t=9.0, b_min_t=0.5)
    )
    with pytest.raises(DeviceGeometryError, match="b_max_t"):
        build(configuration=configuration)


def test_a_field_maximum_away_from_a_throat_is_refused() -> None:
    """A maximum inside the central cell is not a throat and is refused."""
    profile = tuple(
        (height, 8.0 if height == 0.6 else strength)
        for height, strength in reference_field_profile()
    )
    with pytest.raises(DeviceGeometryError, match="outside both mirror coils"):
        build(profile=profile)


def test_a_profile_that_stops_short_of_the_throats_is_refused() -> None:
    """A column that never reaches a throat is not the confined column."""
    with pytest.raises(DeviceGeometryError, match="must cover the throats"):
        build(profile=((-1.0, 8.0), (0.0, 0.5), (1.0, 8.0)))


def test_a_profile_reaching_past_the_vacuum_envelope_is_refused() -> None:
    """The column cannot pass through an end wall."""
    profile = (
        (-2.5, 0.04),
        *reference_field_profile(),
        (2.5, 0.04),
    )
    with pytest.raises(DeviceGeometryError, match="vacuum envelope"):
        build(profile=profile)


def test_a_tube_wider_than_the_throat_bore_is_refused() -> None:
    """The defining refusal of the family: the column must pass the throat."""
    geometry = dataclasses.replace(
        reference_geometry(), mirror_coil_warm_bore_radius_m=0.02
    )
    with pytest.raises(DeviceGeometryError, match="mirror_coil_upstream"):
        build(geometry=geometry)


def test_a_tube_wider_than_the_vessel_bore_is_refused() -> None:
    """The column has to fit the central-cell vessel it sits in."""
    geometry = dataclasses.replace(
        reference_geometry(), central_cell_vessel_bore_radius_m=0.04
    )
    with pytest.raises(DeviceGeometryError, match="central_cell_vessel"):
        build(geometry=geometry)


def test_a_tube_wider_than_the_tank_bore_is_refused() -> None:
    """The fanned-out column has to fit the tank it expands into."""
    geometry = dataclasses.replace(
        reference_geometry(), expander_tank_bore_radius_m=0.1
    )
    with pytest.raises(DeviceGeometryError, match="expander_tank_upstream"):
        build(geometry=geometry)


def test_the_body_inventory_is_enforced_on_the_record() -> None:
    """A record with the wrong bodies or order is refused."""
    model = build()
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        dataclasses.replace(model, meshes=model.meshes[::-1])


def test_a_uniform_field_cannot_be_declared_at_all() -> None:
    """The family forbids the substitute at the configuration, not in prose.

    A column of constant radius would need a field of constant strength,
    and a mirror ratio above one is the defining property the
    configuration validates. So the cylinder this family is not built from
    is unreachable rather than merely discouraged.
    """
    with pytest.raises(ValueError, match="b_max_t"):
        MirrorField(b_max_t=0.5, b_min_t=0.5)
