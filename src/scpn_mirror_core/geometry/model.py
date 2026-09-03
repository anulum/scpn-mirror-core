# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device 3D model record

"""Tier-G1 device 3D model: analytic bodies of one validated design.

The model composes the validated configuration (axial mirror field, cell
layout), the validated device geometry (vessel, coils, expansion tanks,
end walls), the declared midplane plasma radius of the level-0 models and
a **declared axial field profile** into ten named, closed,
outward-oriented triangle meshes on the device axis, regenerated
deterministically from those inputs.

Nine of the ten bodies are surfaces of constant radius. The tenth is not,
and that is the point of this family: the confined plasma of a mirror is
a flux tube, and flux conservation ties its radius to the field along the
axis, so it is built as a surface of revolution through the ``(z, radius)``
profile the declared field implies
(:mod:`scpn_mirror_core.geometry.profile`, and the library's
``geometry_profiles`` kernel). Drawing it as a cylinder would be a body
that cannot exist inside the machine: an axisymmetric mirror's throat
aperture is narrower than its midplane column, and the model refuses a
design in which the column does not pass through it.

The assembly is symmetric about the midplane, so the axial stations are
named once on the positive side and mirrored. Each mirror coil is centred
on a throat at ``+-central_cell_length_m / 2``, the central-cell vessel
spans between their inboard faces, the two central-cell coils are wound
around the vessel at a declared offset, each expansion tank starts at the
outboard face of its mirror coil, and each end wall closes its tank.

The canonical record carries the schema identity, the units and axis
convention, both source digests, the declared midplane radius, the
declared field profile, the flux-tube profile it implies, the per-section
aperture clearances, the segment count, a summary of every body (counts,
volume, area, bounding box, mesh digest) and fixed non-claims; the
SHA-256 of that record identifies the exact model.

The unit circle, the primitives, the profiled surface of revolution and
the mesh contract are consumed from the pinned shared kernel library
(``scpn_reactor_kernels.geometry``, ADR 0006 here, ADR 0010 there); this
module owns only the device composition.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import (
    Profile,
    TriangleMesh,
    annular_tube,
    cylinder_solid,
    profiled_solid,
    require_segments,
)

from scpn_mirror_core.configuration import DeviceConfiguration
from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.geometry.device import DeviceGeometry
from scpn_mirror_core.geometry.profile import (
    FIELD_MATCH_RELATIVE_TOLERANCE,
    ApertureSection,
    FieldProfile,
    FluxTubeClearance,
    flux_tube_clearances,
    flux_tube_profile,
    midplane_field_t,
    require_field_profile,
    throat_field_t,
)
from scpn_mirror_core.parameters import require_positive

MODEL_SCHEMA: Final = "scpn.mirror-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "magnetic_flux_density": "tesla",
    "handedness": "right",
    "axis": "z along the device axis, increasing downstream",
    "origin": "central-cell midplane at z = 0 on the axis",
}
MODEL_NON_CLAIMS: Final = (
    (
        "analytic surfaces tessellated from a declared configuration, geometry"
        " and axial field profile"
    ),
    (
        "the flux tube is the surface of revolution of the DECLARED field"
        " profile under flux conservation: not an equilibrium boundary, not an"
        " anisotropic-pressure solution, not a prediction of any machine"
    ),
    (
        "the field profile is linear between the samples it is given; no local"
        " field structure between samples is resolved and no field is solved"
    ),
    (
        "the coils are annular winding envelopes: no conductor layout, no"
        " current, no force and no cryostat is modelled"
    ),
    "no material property, load, field or neutronic quantity is carried",
    (
        "the end walls are closing discs; pumping ducts, limiters, end rings"
        " and heating hardware are not modelled"
    ),
    (
        "a dimension reproduced from a published arrangement is an anchor,"
        " not a claim about that machine"
    ),
)

ROLE_COIL: Final = "coil"
ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_PLASMA: Final = "plasma"
MATERIAL_COIL_CONDUCTOR: Final = "coil_conductor"
MATERIAL_VESSEL_WALL: Final = "vessel_wall"
MATERIAL_END_WALL: Final = "end_wall"
MATERIAL_PLASMA: Final = "plasma"

BODY_CENTRAL_CELL_VESSEL: Final = "central_cell_vessel"
BODY_CENTRAL_CELL_COIL_UPSTREAM: Final = "central_cell_coil_upstream"
BODY_CENTRAL_CELL_COIL_DOWNSTREAM: Final = "central_cell_coil_downstream"
BODY_MIRROR_COIL_UPSTREAM: Final = "mirror_coil_upstream"
BODY_MIRROR_COIL_DOWNSTREAM: Final = "mirror_coil_downstream"
BODY_EXPANDER_TANK_UPSTREAM: Final = "expander_tank_upstream"
BODY_EXPANDER_TANK_DOWNSTREAM: Final = "expander_tank_downstream"
BODY_END_WALL_UPSTREAM: Final = "end_wall_upstream"
BODY_END_WALL_DOWNSTREAM: Final = "end_wall_downstream"
BODY_PLASMA_FLUX_TUBE: Final = "plasma_flux_tube"
BODY_NAMES: Final = (
    BODY_CENTRAL_CELL_VESSEL,
    BODY_CENTRAL_CELL_COIL_UPSTREAM,
    BODY_CENTRAL_CELL_COIL_DOWNSTREAM,
    BODY_MIRROR_COIL_UPSTREAM,
    BODY_MIRROR_COIL_DOWNSTREAM,
    BODY_EXPANDER_TANK_UPSTREAM,
    BODY_EXPANDER_TANK_DOWNSTREAM,
    BODY_END_WALL_UPSTREAM,
    BODY_END_WALL_DOWNSTREAM,
    BODY_PLASMA_FLUX_TUBE,
)


@dataclass(frozen=True, slots=True)
class AxialStations:
    """Axial stations of the assembly, named once on the positive side.

    The machine is symmetric about the midplane, so every station below
    has its mirror image at the negative value and the model reads the
    two coils, the two tanks and the two end walls off the same numbers.

    Parameters
    ----------
    vessel_end_m
        Inboard face of a mirror coil, which is where the central-cell
        vessel ends: ``L / 2 - mirror_coil_length_m / 2``.
    throat_m
        Centre of a mirror coil, the throat: ``L / 2``.
    coil_end_m
        Outboard face of a mirror coil, where its expansion tank starts.
    expander_end_m
        Outboard face of an expansion tank, where its end wall starts.
    end_wall_end_m
        Outboard face of an end wall, the axial extent of the assembly.
    central_cell_coil_low_m, central_cell_coil_high_m
        Inboard and outboard faces of the downstream central-cell coil.
    """

    vessel_end_m: float
    throat_m: float
    coil_end_m: float
    expander_end_m: float
    end_wall_end_m: float
    central_cell_coil_low_m: float
    central_cell_coil_high_m: float


def axial_stations(
    configuration: DeviceConfiguration, geometry: DeviceGeometry
) -> AxialStations:
    """Derive the axial stations of a validated design.

    Parameters
    ----------
    configuration
        Validated configuration; its ``layout.central_cell_length_m`` is
        the throat-to-throat separation and the only source of it.
    geometry
        Validated device geometry.

    Returns
    -------
    AxialStations
        The stations of the positive half of the assembly.

    Raises
    ------
    DeviceGeometryError
        If the central cell is not longer than a mirror coil (the coils
        would meet or cross at the midplane), or if the central-cell
        coils would cross the midplane or fall outside the vessel.
    """
    half = configuration.layout.central_cell_length_m / 2.0
    coil_half = geometry.mirror_coil_length_m / 2.0
    if configuration.layout.central_cell_length_m <= geometry.mirror_coil_length_m:
        raise DeviceGeometryError(
            "central_cell_length_m: must exceed mirror_coil_length_m "
            f"({configuration.layout.central_cell_length_m!r} <= "
            f"{geometry.mirror_coil_length_m!r}) — the vessel spans between "
            "the coils' inboard faces and would have no length"
        )
    vessel_end = half - coil_half
    trim_half = geometry.central_cell_coil_length_m / 2.0
    trim_low = geometry.central_cell_coil_offset_m - trim_half
    trim_high = geometry.central_cell_coil_offset_m + trim_half
    if trim_low <= 0.0:
        raise DeviceGeometryError(
            "central_cell_coil_offset_m: must exceed half the coil length "
            f"({geometry.central_cell_coil_offset_m!r} <= {trim_half!r}) — the "
            "two central-cell coils would meet or cross at the midplane"
        )
    if trim_high > vessel_end:
        raise DeviceGeometryError(
            "central_cell_coil_offset_m: the coil must stay inside the "
            f"central cell, whose vessel ends at {vessel_end!r}, got an "
            f"outboard face at {trim_high!r}"
        )
    return AxialStations(
        vessel_end_m=vessel_end,
        throat_m=half,
        coil_end_m=half + coil_half,
        expander_end_m=half + coil_half + geometry.expander_tank_length_m,
        end_wall_end_m=half
        + coil_half
        + geometry.expander_tank_length_m
        + geometry.end_wall_thickness_m,
        central_cell_coil_low_m=trim_low,
        central_cell_coil_high_m=trim_high,
    )


def aperture_sections(
    geometry: DeviceGeometry, stations: AxialStations
) -> tuple[ApertureSection, ...]:
    """Return the five aperture sections of the assembly, in ascending ``z``.

    Parameters
    ----------
    geometry
        Validated device geometry, which carries the three bores.
    stations
        Axial stations of the design.

    Returns
    -------
    tuple of ApertureSection
        Upstream tank, upstream throat, central cell, downstream throat,
        downstream tank — each with the bore the flux tube clears there.
    """
    return (
        ApertureSection(
            name=BODY_EXPANDER_TANK_UPSTREAM,
            z_low_m=-stations.expander_end_m,
            z_high_m=-stations.coil_end_m,
            bore_radius_m=geometry.expander_tank_bore_radius_m,
        ),
        ApertureSection(
            name=BODY_MIRROR_COIL_UPSTREAM,
            z_low_m=-stations.coil_end_m,
            z_high_m=-stations.vessel_end_m,
            bore_radius_m=geometry.mirror_coil_warm_bore_radius_m,
        ),
        ApertureSection(
            name=BODY_CENTRAL_CELL_VESSEL,
            z_low_m=-stations.vessel_end_m,
            z_high_m=stations.vessel_end_m,
            bore_radius_m=geometry.central_cell_vessel_bore_radius_m,
        ),
        ApertureSection(
            name=BODY_MIRROR_COIL_DOWNSTREAM,
            z_low_m=stations.vessel_end_m,
            z_high_m=stations.coil_end_m,
            bore_radius_m=geometry.mirror_coil_warm_bore_radius_m,
        ),
        ApertureSection(
            name=BODY_EXPANDER_TANK_DOWNSTREAM,
            z_low_m=stations.coil_end_m,
            z_high_m=stations.expander_end_m,
            bore_radius_m=geometry.expander_tank_bore_radius_m,
        ),
    )


def _check_profile_against_configuration(
    configuration: DeviceConfiguration,
    profile: FieldProfile,
    stations: AxialStations,
) -> float:
    """Cross-check a declared field profile against the validated configuration.

    Parameters
    ----------
    configuration
        Validated configuration, whose ``field`` declares the midplane
        and throat fields the profile has to reproduce.
    profile
        Validated declared field profile.
    stations
        Axial stations of the design.

    Returns
    -------
    float
        The declared midplane field, which is the reference the flux-tube
        radius is taken at.

    Raises
    ------
    DeviceGeometryError
        If the midplane sample does not carry the configuration's
        ``b_min_t``, if the largest sample does not carry its
        ``b_max_t``, if a sample carrying the largest field sits outside
        a mirror coil (a maximum away from a throat is not a throat), if
        the profile does not reach both throats, or if it extends past
        the vacuum envelope into an end wall.
    """
    reference = midplane_field_t("field_profile", profile)
    declared = configuration.field
    if not math.isclose(
        reference, declared.b_min_t, rel_tol=FIELD_MATCH_RELATIVE_TOLERANCE
    ):
        raise DeviceGeometryError(
            "field_profile: the sample at z = 0.0 must carry the "
            f"configuration's b_min_t {declared.b_min_t!r}, got {reference!r}"
        )
    throat = throat_field_t(profile)
    if not math.isclose(
        throat, declared.b_max_t, rel_tol=FIELD_MATCH_RELATIVE_TOLERANCE
    ):
        raise DeviceGeometryError(
            "field_profile: the largest sample must carry the configuration's "
            f"b_max_t {declared.b_max_t!r}, got {throat!r}"
        )
    for height, strength in profile:
        if not math.isclose(strength, throat, rel_tol=FIELD_MATCH_RELATIVE_TOLERANCE):
            continue
        inside_upstream = -stations.coil_end_m <= height <= -stations.vessel_end_m
        inside_downstream = stations.vessel_end_m <= height <= stations.coil_end_m
        if not (inside_upstream or inside_downstream):
            raise DeviceGeometryError(
                f"field_profile: the largest field {strength!r} T sits at "
                f"z = {height!r}, outside both mirror coils "
                f"([{-stations.coil_end_m!r}, {-stations.vessel_end_m!r}] and "
                f"[{stations.vessel_end_m!r}, {stations.coil_end_m!r}]) — a "
                "field maximum away from a throat is not a throat"
            )
    if profile[0][0] > -stations.throat_m or profile[-1][0] < stations.throat_m:
        raise DeviceGeometryError(
            "field_profile: must cover the throats at "
            f"z = -+{stations.throat_m!r}, got "
            f"[{profile[0][0]!r}, {profile[-1][0]!r}] — a column that stops "
            "short of a throat is not the confined column"
        )
    if profile[0][0] < -stations.expander_end_m or (
        profile[-1][0] > stations.expander_end_m
    ):
        raise DeviceGeometryError(
            "field_profile: must stay inside the vacuum envelope "
            f"[{-stations.expander_end_m!r}, {stations.expander_end_m!r}], got "
            f"[{profile[0][0]!r}, {profile[-1][0]!r}] — the column cannot pass "
            "through an end wall"
        )
    return reference


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one validated mirror design.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    midplane_plasma_radius_m
        Declared plasma radius at the midplane the flux tube was built
        from.
    field_profile
        The declared axial field profile, as given.
    tube_profile
        The ``(z, radius)`` flux-tube profile the declared field implies
        under flux conservation.
    clearances
        Per-section aperture clearances of the flux tube, in section
        order, for the sections the tube enters.
    segments
        Circumferential segment count used for every body.
    meshes
        The ten bodies in the fixed order of :data:`BODY_NAMES`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :data:`BODY_NAMES`.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    midplane_plasma_radius_m: float
    field_profile: FieldProfile
    tube_profile: Profile
    clearances: tuple[FluxTubeClearance, ...]
    segments: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body inventory.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from
            :data:`BODY_NAMES`.
        """
        names = tuple(mesh.name for mesh in self.meshes)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, the
            declared midplane radius, the declared field profile, the
            flux-tube profile, the aperture clearances, the segment count
            and every body summary.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "midplane_plasma_radius_m": self.midplane_plasma_radius_m,
            "field_profile": [list(sample) for sample in self.field_profile],
            "flux_tube_profile": [list(sample) for sample in self.tube_profile],
            "flux_tube_clearances": [item.to_record() for item in self.clearances],
            "segments": self.segments,
            "bodies": [mesh.summary_record() for mesh in self.meshes],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

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
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _tessellated_bodies(
    geometry: DeviceGeometry,
    stations: AxialStations,
    tube_profile: Profile,
    segments: int,
) -> tuple[TriangleMesh, ...]:
    """Tessellate the ten bodies of a checked design, in the fixed order.

    Parameters
    ----------
    geometry
        Validated device geometry.
    stations
        Axial stations of the design.
    tube_profile
        The flux-tube ``(z, radius)`` profile.
    segments
        Circumferential segments for every body.

    Returns
    -------
    tuple of TriangleMesh
        The bodies in the order of :data:`BODY_NAMES`.
    """
    vessel_outer = geometry.central_cell_vessel_outer_radius_m
    trim_bore = geometry.central_cell_coil_bore_radius_m
    trim_outer = geometry.central_cell_coil_outer_radius_m
    warm_bore = geometry.mirror_coil_warm_bore_radius_m
    mirror_outer = geometry.mirror_coil_outer_radius_m
    tank_bore = geometry.expander_tank_bore_radius_m
    tank_outer = geometry.expander_tank_outer_radius_m
    bodies = (
        (
            BODY_CENTRAL_CELL_VESSEL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_VESSEL_WALL,
            annular_tube(
                geometry.central_cell_vessel_bore_radius_m,
                vessel_outer,
                -stations.vessel_end_m,
                stations.vessel_end_m,
                segments,
            ),
        ),
        (
            BODY_CENTRAL_CELL_COIL_UPSTREAM,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                trim_bore,
                trim_outer,
                -stations.central_cell_coil_high_m,
                -stations.central_cell_coil_low_m,
                segments,
            ),
        ),
        (
            BODY_CENTRAL_CELL_COIL_DOWNSTREAM,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                trim_bore,
                trim_outer,
                stations.central_cell_coil_low_m,
                stations.central_cell_coil_high_m,
                segments,
            ),
        ),
        (
            BODY_MIRROR_COIL_UPSTREAM,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                warm_bore,
                mirror_outer,
                -stations.coil_end_m,
                -stations.vessel_end_m,
                segments,
            ),
        ),
        (
            BODY_MIRROR_COIL_DOWNSTREAM,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                warm_bore,
                mirror_outer,
                stations.vessel_end_m,
                stations.coil_end_m,
                segments,
            ),
        ),
        (
            BODY_EXPANDER_TANK_UPSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_VESSEL_WALL,
            annular_tube(
                tank_bore,
                tank_outer,
                -stations.expander_end_m,
                -stations.coil_end_m,
                segments,
            ),
        ),
        (
            BODY_EXPANDER_TANK_DOWNSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_VESSEL_WALL,
            annular_tube(
                tank_bore,
                tank_outer,
                stations.coil_end_m,
                stations.expander_end_m,
                segments,
            ),
        ),
        (
            BODY_END_WALL_UPSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_END_WALL,
            cylinder_solid(
                tank_outer,
                -stations.end_wall_end_m,
                -stations.expander_end_m,
                segments,
            ),
        ),
        (
            BODY_END_WALL_DOWNSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_END_WALL,
            cylinder_solid(
                tank_outer,
                stations.expander_end_m,
                stations.end_wall_end_m,
                segments,
            ),
        ),
        (
            BODY_PLASMA_FLUX_TUBE,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            profiled_solid(tube_profile, segments),
        ),
    )
    return tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )


def build_device_model(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    midplane_plasma_radius_m: float,
    field_profile: FieldProfile,
    segments: int,
) -> DeviceModel3D:
    """Tessellate the ten bodies of a validated mirror design.

    Parameters
    ----------
    configuration
        Validated mirror configuration; its cell layout fixes the
        throat-to-throat separation and its field declares the midplane
        and throat field strengths the profile has to reproduce.
    geometry
        Validated device geometry (vessel, coils, tanks, end walls).
    midplane_plasma_radius_m
        Declared plasma radius at the midplane, the quantity the level-0
        models take; strictly positive.
    field_profile
        Declared ordered ``(z, B)`` samples of the axial field. Declared,
        never invented: the geometry applies flux conservation to it and
        nothing else.
    segments
        Circumferential segments for every body; at least 8, multiple
        of 8.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid, if the midplane radius is not
        strictly positive, if the field profile violates its contract or
        contradicts the configuration, or if the flux tube does not clear
        an aperture it passes through. The shared library's refusals are
        re-raised under the device error type with their messages.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    try:
        require_positive("midplane_plasma_radius_m", midplane_plasma_radius_m)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    require_field_profile("field_profile", field_profile)
    stations = axial_stations(configuration, geometry)
    reference_field = _check_profile_against_configuration(
        configuration, field_profile, stations
    )
    tube_profile = flux_tube_profile(
        field_profile, midplane_plasma_radius_m, reference_field
    )
    clearances = flux_tube_clearances(
        aperture_sections(geometry, stations), tube_profile
    )
    # every precondition of the library primitives is established above: the
    # segment rule, both wall thicknesses (outer radius above inner), the
    # station ordering (a cell longer than a coil, positive tank and wall
    # lengths) and the profile contract. A handler here would claim a failure
    # mode that cannot occur, so there is none.
    meshes = _tessellated_bodies(geometry, stations, tube_profile, segments)
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        midplane_plasma_radius_m=midplane_plasma_radius_m,
        field_profile=tuple(field_profile),
        tube_profile=tube_profile,
        clearances=clearances,
        segments=segments,
        meshes=meshes,
    )
