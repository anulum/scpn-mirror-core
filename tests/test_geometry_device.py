# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device geometry tests

"""Validation, envelope relations, canonical serialisation and digest identity.

Every declared field is checked for the positivity rule, both envelope
relations are checked in the direction they refuse, and the record is
checked as a round trip. All values are synthetic.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math

import pytest

from geometry_fixtures import anchor_geometry, reference_geometry
from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.geometry import (
    GEOMETRY_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)


def test_every_declared_field_is_in_the_field_tuple() -> None:
    """The field tuple is the dataclass field list, in order."""
    assert (
        tuple(item.name for item in dataclasses.fields(DeviceGeometry))
        == GEOMETRY_FIELDS
    )


@pytest.mark.parametrize("name", GEOMETRY_FIELDS)
@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf, -math.inf])
def test_each_field_refuses_non_positive_and_non_finite(
    name: str, value: float
) -> None:
    """Every declared parameter fails closed on a non-positive or NaN value."""
    with pytest.raises(DeviceGeometryError, match=name):
        dataclasses.replace(reference_geometry(), **{name: value})


def test_outer_radii_are_bore_plus_thickness() -> None:
    """The four derived radii are the declared sums, exactly."""
    geometry = reference_geometry()
    assert geometry.central_cell_vessel_outer_radius_m == (
        geometry.central_cell_vessel_bore_radius_m
        + geometry.central_cell_vessel_wall_thickness_m
    )
    assert geometry.central_cell_coil_outer_radius_m == (
        geometry.central_cell_coil_bore_radius_m
        + geometry.central_cell_coil_winding_thickness_m
    )
    assert geometry.mirror_coil_outer_radius_m == (
        geometry.mirror_coil_warm_bore_radius_m
        + geometry.mirror_coil_winding_thickness_m
    )
    assert geometry.expander_tank_outer_radius_m == (
        geometry.expander_tank_bore_radius_m + geometry.expander_tank_wall_thickness_m
    )


def test_a_central_cell_coil_inside_the_vessel_wall_is_refused() -> None:
    """A trim coil whose bore is under the vessel outer radius fails closed."""
    geometry = reference_geometry()
    with pytest.raises(DeviceGeometryError, match="central_cell_coil_bore_radius_m"):
        dataclasses.replace(
            geometry,
            central_cell_coil_bore_radius_m=(
                geometry.central_cell_vessel_outer_radius_m - 1.0e-6
            ),
        )


def test_a_coil_bore_flush_with_the_vessel_wall_is_accepted() -> None:
    """The relation is an inequality: a coil wound flush on the wall is legal."""
    geometry = reference_geometry()
    flush = dataclasses.replace(
        geometry,
        central_cell_coil_bore_radius_m=geometry.central_cell_vessel_outer_radius_m,
    )
    assert flush.central_cell_coil_bore_radius_m == (
        geometry.central_cell_vessel_outer_radius_m
    )


@pytest.mark.parametrize("bore", [0.06, 0.02])
def test_a_tank_no_wider_than_the_throat_is_refused(bore: float) -> None:
    """A tank at or below the warm bore is not an expander and is refused."""
    with pytest.raises(DeviceGeometryError, match="expander_tank_bore_radius_m"):
        dataclasses.replace(reference_geometry(), expander_tank_bore_radius_m=bore)


def test_record_round_trip_and_digest_identity() -> None:
    """The record round-trips through JSON and the digest is its SHA-256."""
    geometry = reference_geometry()
    record = geometry.to_record()
    assert sorted(record) == sorted(GEOMETRY_FIELDS)
    data = geometry.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert geometry.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert geometry_from_record(record) == geometry
    assert geometry_from_bytes(data) == geometry


def test_two_designs_have_different_digests() -> None:
    """The digest identifies the exact geometry, not the schema."""
    assert reference_geometry().digest_sha256() != anchor_geometry().digest_sha256()


def test_record_refuses_a_foreign_shape() -> None:
    """A non-object, an unknown field and a non-number all fail closed."""
    with pytest.raises(DeviceGeometryError, match="must be an object"):
        geometry_from_record([1, 2, 3])
    record = reference_geometry().to_record()
    with pytest.raises(DeviceGeometryError, match="unknown fields"):
        geometry_from_record({**record, "coil_current_a": 2000.0})
    with pytest.raises(DeviceGeometryError, match="end_wall_thickness_m"):
        geometry_from_record({**record, "end_wall_thickness_m": "0.05"})
    with pytest.raises(DeviceGeometryError, match="end_wall_thickness_m"):
        geometry_from_record({**record, "end_wall_thickness_m": True})


def test_bytes_refuse_invalid_documents_and_non_finite_literals() -> None:
    """Malformed JSON and NaN or Infinity literals are refused, never parsed."""
    with pytest.raises(DeviceGeometryError, match="invalid JSON document"):
        geometry_from_bytes(b"{")
    with pytest.raises(DeviceGeometryError, match="invalid JSON document"):
        geometry_from_bytes(b"\xff\xfe")
    record = reference_geometry().to_record()
    text = json.dumps({**record, "end_wall_thickness_m": float("nan")})
    with pytest.raises(DeviceGeometryError, match="non-finite JSON literal"):
        geometry_from_bytes(text.encode("utf-8"))


def test_a_missing_field_is_refused() -> None:
    """A record short of one declared field fails closed on that field."""
    record = reference_geometry().to_record()
    del record["mirror_coil_length_m"]
    with pytest.raises(DeviceGeometryError, match="mirror_coil_length_m"):
        geometry_from_record(record)
