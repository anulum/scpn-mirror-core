# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device geometry model

"""Validated mechanical envelope of an axisymmetric magnetic-mirror assembly.

The geometry complements the
:class:`~scpn_mirror_core.configuration.DeviceConfiguration` (which
carries the axial mirror field and the cell layout) with the
device-owned mechanical envelope: the central-cell vacuum vessel, the
pair of central-cell coils that set the field at the midplane, the pair
of mirror coils that close the cell, the expansion tanks beyond them and
the end walls that close those. The layout is the arrangement of an
axisymmetric mirror with an expander at each end, described for the
Wisconsin HTS Axisymmetric Mirror by D. Endrizzi et al., "Physics basis
for the Wisconsin HTS Axisymmetric Mirror (WHAM)", J. Plasma Phys. 89
(2023) 975890501 (CC BY 4.0), sections 2, 2.1 and 2.2: a central cell
"bounded on either end by the HTS mirror magnets, which are in turn
bookended by large expansion tank end cells", with two further coils
near the midplane that raise the central field. Parameter sets are
declared by the caller: the repository's own fixtures are synthetic, and
one anchor fixture carries the dimensions that paper prints so the tier
can be checked against a published arrangement. Reproducing a printed
dimension is an anchor, never a claim about that machine.

The mirror-coil axial positions are not repeated here. They are the
throats of the validated configuration's
:class:`~scpn_mirror_core.parameters.CellLayout`: each mirror coil is
centred at ``+-central_cell_length_m / 2``, so the cell length and the
coil separation are one number with one home, read from the
configuration when the model is built. Validation is fail-closed,
serialisation is canonical, and the SHA-256 digest identifies the exact
geometry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.parameters import require_positive

GEOMETRY_FIELDS: Final = (
    "central_cell_vessel_bore_radius_m",
    "central_cell_vessel_wall_thickness_m",
    "central_cell_coil_offset_m",
    "central_cell_coil_bore_radius_m",
    "central_cell_coil_winding_thickness_m",
    "central_cell_coil_length_m",
    "mirror_coil_warm_bore_radius_m",
    "mirror_coil_winding_thickness_m",
    "mirror_coil_length_m",
    "expander_tank_bore_radius_m",
    "expander_tank_wall_thickness_m",
    "expander_tank_length_m",
    "end_wall_thickness_m",
)


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule with the geometry error type.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceGeometryError
        If the value is non-finite or not strictly positive.
    """
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceGeometry:
    """Validated magnetic-mirror envelope (SI units in the field names).

    Parameters
    ----------
    central_cell_vessel_bore_radius_m
        Bore radius of the central-cell vacuum vessel; strictly positive.
    central_cell_vessel_wall_thickness_m
        Radial wall thickness of the central-cell vessel; strictly
        positive.
    central_cell_coil_offset_m
        Axial distance of each central-cell coil centre from the
        midplane; strictly positive.
    central_cell_coil_bore_radius_m
        Bore radius of each central-cell coil; strictly positive, and at
        least the vessel outer radius because the coil is wound around
        the vessel.
    central_cell_coil_winding_thickness_m
        Radial winding thickness of each central-cell coil; strictly
        positive.
    central_cell_coil_length_m
        Axial length of each central-cell coil; strictly positive.
    mirror_coil_warm_bore_radius_m
        Warm-bore radius of each mirror coil, the narrowest aperture of
        the assembly; strictly positive.
    mirror_coil_winding_thickness_m
        Radial winding thickness of each mirror coil; strictly positive.
    mirror_coil_length_m
        Axial length of each mirror coil; strictly positive.
    expander_tank_bore_radius_m
        Bore radius of each expansion tank; strictly positive and
        strictly larger than the mirror-coil warm bore, which is what
        makes the tank an expander.
    expander_tank_wall_thickness_m
        Radial wall thickness of each expansion tank; strictly positive.
    expander_tank_length_m
        Axial length of each expansion tank; strictly positive.
    end_wall_thickness_m
        Axial thickness of the two end walls; strictly positive.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive, if a
        central-cell coil would sit inside the vessel wall, or if an
        expansion tank is not wider than the throat it opens from.
    """

    central_cell_vessel_bore_radius_m: float
    central_cell_vessel_wall_thickness_m: float
    central_cell_coil_offset_m: float
    central_cell_coil_bore_radius_m: float
    central_cell_coil_winding_thickness_m: float
    central_cell_coil_length_m: float
    mirror_coil_warm_bore_radius_m: float
    mirror_coil_winding_thickness_m: float
    mirror_coil_length_m: float
    expander_tank_bore_radius_m: float
    expander_tank_wall_thickness_m: float
    expander_tank_length_m: float
    end_wall_thickness_m: float

    def __post_init__(self) -> None:
        """Validate every declared value and the two envelope relations.

        Raises
        ------
        DeviceGeometryError
            If any value is non-finite or not strictly positive, if a
            central-cell coil would sit inside the vessel wall, or if an
            expansion tank is not wider than the throat.
        """
        for name in GEOMETRY_FIELDS:
            _positive(name, getattr(self, name))
        vessel_outer = self.central_cell_vessel_outer_radius_m
        if self.central_cell_coil_bore_radius_m < vessel_outer:
            raise DeviceGeometryError(
                "central_cell_coil_bore_radius_m: must be at least the vessel "
                f"outer radius {vessel_outer!r}, got "
                f"{self.central_cell_coil_bore_radius_m!r} — the coil is wound "
                "around the vessel, not inside it"
            )
        if self.expander_tank_bore_radius_m <= self.mirror_coil_warm_bore_radius_m:
            raise DeviceGeometryError(
                "expander_tank_bore_radius_m: must be strictly larger than "
                f"mirror_coil_warm_bore_radius_m "
                f"({self.expander_tank_bore_radius_m!r} <= "
                f"{self.mirror_coil_warm_bore_radius_m!r}) — a tank that does "
                "not open out beyond the throat is not an expander"
            )

    @property
    def central_cell_vessel_outer_radius_m(self) -> float:
        """Outer radius of the central-cell vessel (bore plus wall)."""
        return (
            self.central_cell_vessel_bore_radius_m
            + self.central_cell_vessel_wall_thickness_m
        )

    @property
    def central_cell_coil_outer_radius_m(self) -> float:
        """Outer radius of a central-cell coil (bore plus winding)."""
        return (
            self.central_cell_coil_bore_radius_m
            + self.central_cell_coil_winding_thickness_m
        )

    @property
    def mirror_coil_outer_radius_m(self) -> float:
        """Outer radius of a mirror coil (warm bore plus winding)."""
        return (
            self.mirror_coil_warm_bore_radius_m + self.mirror_coil_winding_thickness_m
        )

    @property
    def expander_tank_outer_radius_m(self) -> float:
        """Outer radius of an expansion tank (bore plus wall)."""
        return self.expander_tank_bore_radius_m + self.expander_tank_wall_thickness_m

    def to_record(self) -> dict[str, float]:
        """Project the geometry to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in GEOMETRY_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the geometry canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact geometry.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Decoded JSON object.
    field
        Field name to read.

    Returns
    -------
    float
        The field value as a float.

    Raises
    ------
    DeviceGeometryError
        If the field is missing or not a real number (booleans rejected).
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceGeometryError(f"{field}: must be a number, got {value!r}")
    return float(value)


def geometry_from_record(record: Any) -> DeviceGeometry:
    """Build a validated geometry from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceGeometry.to_record`.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the record shape or any value violates the model; unknown
        fields are refused.
    """
    if not isinstance(record, dict):
        raise DeviceGeometryError("record: must be an object")
    unknown = sorted(set(record) - set(GEOMETRY_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"record: unknown fields {unknown!r}")
    return DeviceGeometry(**{name: _number(record, name) for name in GEOMETRY_FIELDS})


def geometry_from_bytes(data: bytes) -> DeviceGeometry:
    """Build a validated geometry from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceGeometryError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceGeometryError(f"record: invalid JSON document: {exc}") from exc
    return geometry_from_record(record)
