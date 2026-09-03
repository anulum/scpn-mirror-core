# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device CAD model tests (tier G2)

"""B-rep agreement, faceting bounds, STEP determinism and record identity.

The reference set is synthetic and describes no machine. The anchor set
carries the dimensions the filed WHAM physics basis prints, and the
anchor test here proves the revolved flux tube passes the printed bore as
a B-rep solid, not only as a tessellation. The B-rep measures come from
the pinned third-party OpenCASCADE kernel and are checked against the
analytic closed forms within the library's declared tolerance — for the
flux tube that closed form is the exact frustum-stack sum of its linear
profile, which is why the check is an agreement and not a convergence.
The tier-G1 reference mesh, the polygon-deficit bound and the per-body
evidence come from the shared kernel library.
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("cadquery")

from scpn_reactor_kernels.cad import MANIFEST_SCHEMA, MEASURE_TOLERANCE
from scpn_reactor_kernels.errors import CadError

from geometry_fixtures import (
    ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
    ANCHOR_THROAT_POSITION_M,
    ANCHOR_WARM_BORE_RADIUS_M,
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    anchor_configuration,
    anchor_field_profile,
    anchor_geometry,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
)
from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.geometry import (
    BODY_NAMES,
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModelCAD,
    axial_stations,
    build_device_cad,
    build_device_model,
    write_step,
)

#: Digest of the reference CAD model record in the pinned back-end
#: environment (cadquery 2.8.0, OCP 7.9.3.1); a back-end bump re-pins it
#: as a governed data change (ADR 0008).
REFERENCE_CAD_MODEL_SHA256 = (
    "d6e7bba273cb158e81d7997d47d14580d00493847af4952e7ee759fd1feaa25f"
)


@functools.cache
def reference_cad_model() -> DeviceModelCAD:
    """Build the synthetic CAD model of the tests once.

    The record is a frozen dataclass of immutable members, so caching one
    build is a cache of a value, not shared mutable state; the tests that
    vary it build replacements with :func:`dataclasses.replace`.
    """
    return build_device_cad(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
    )


@functools.cache
def anchor_cad_model() -> DeviceModelCAD:
    """Build the anchor CAD model of the printed arrangement once."""
    return build_device_cad(
        anchor_configuration(),
        anchor_geometry(),
        ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
        anchor_field_profile(),
    )


def analytic_volumes() -> tuple[float, ...]:
    """Return the closed-form volume of every body of the reference design.

    The expressions are the closed forms of the library's primitives in
    its own operation order (``pi (r_o r_o - r_i r_i) h`` for a tube,
    ``pi r r h`` for a disc, and the frustum-stack sum for the profiled
    flux tube), evaluated on the same fixture values the build reads, so
    the comparison is an exact equality and not an approximation. Writing
    the numbers as decimal literals would not be: the axial extents are
    differences of fixture values whose binary result is not the decimal
    one.
    """
    geometry = reference_geometry()
    stations = axial_stations(reference_configuration(), geometry)
    vessel_bore = geometry.central_cell_vessel_bore_radius_m
    vessel_outer = geometry.central_cell_vessel_outer_radius_m
    trim_bore = geometry.central_cell_coil_bore_radius_m
    trim_outer = geometry.central_cell_coil_outer_radius_m
    warm_bore = geometry.mirror_coil_warm_bore_radius_m
    mirror_outer = geometry.mirror_coil_outer_radius_m
    tank_bore = geometry.expander_tank_bore_radius_m
    tank_outer = geometry.expander_tank_outer_radius_m
    trim_length = stations.central_cell_coil_high_m - stations.central_cell_coil_low_m
    coil_length = stations.coil_end_m - stations.vessel_end_m
    tank_length = stations.expander_end_m - stations.coil_end_m
    wall_length = stations.end_wall_end_m - stations.expander_end_m
    tube = 0.0
    profile = reference_cad_model().tube_profile
    for index in range(len(profile) - 1):
        low_z, low_radius = profile[index]
        high_z, high_radius = profile[index + 1]
        tube += (
            (math.pi / 3.0)
            * (
                low_radius * low_radius
                + low_radius * high_radius
                + high_radius * high_radius
            )
            * (high_z - low_z)
        )
    return (
        math.pi
        * (vessel_outer * vessel_outer - vessel_bore * vessel_bore)
        * (2.0 * stations.vessel_end_m),
        math.pi * (trim_outer * trim_outer - trim_bore * trim_bore) * trim_length,
        math.pi * (trim_outer * trim_outer - trim_bore * trim_bore) * trim_length,
        math.pi * (mirror_outer * mirror_outer - warm_bore * warm_bore) * coil_length,
        math.pi * (mirror_outer * mirror_outer - warm_bore * warm_bore) * coil_length,
        math.pi * (tank_outer * tank_outer - tank_bore * tank_bore) * tank_length,
        math.pi * (tank_outer * tank_outer - tank_bore * tank_bore) * tank_length,
        math.pi * tank_outer * tank_outer * wall_length,
        math.pi * tank_outer * tank_outer * wall_length,
        tube,
    )


def test_bodies_match_the_g1_inventory_roles_and_materials() -> None:
    """The CAD bodies are the G1 bodies: same names, roles, materials."""
    model = reference_cad_model()
    reference = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        DEFAULT_REFERENCE_MESH_SEGMENTS,
    )
    assert tuple(body.name for body in model.bodies) == BODY_NAMES
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.role == mesh.role
        assert body.material_identifier == mesh.material_identifier


def test_the_two_tiers_describe_one_flux_tube() -> None:
    """The revolved tube and the tessellated tube come from the same profile."""
    model = reference_cad_model()
    reference = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        DEFAULT_REFERENCE_MESH_SEGMENTS,
    )
    assert model.tube_profile == reference.tube_profile
    assert model.field_profile == reference.field_profile
    assert model.clearances == reference.clearances


def test_brep_measures_agree_with_the_analytic_closed_forms() -> None:
    """Every body volume and area matches the analytic form within 1e-9."""
    model = reference_cad_model()
    for body, analytic in zip(model.bodies, analytic_volumes(), strict=True):
        assert body.analytic_volume_m3 == analytic, body.name
        assert 0.0 <= body.volume_relative_error <= MEASURE_TOLERANCE
        assert 0.0 <= body.surface_area_relative_error <= MEASURE_TOLERANCE


def test_faceted_volumes_stay_within_the_deflection_deficit_bound() -> None:
    """The faceted body underestimates the analytic volume within 2 d / r."""
    model = reference_cad_model()
    for body in model.bodies:
        assert body.faceted_volume_relative_deficit >= 0.0
        assert body.faceted_volume_relative_deficit <= body.faceted_volume_deficit_bound
        assert body.faceted_volume_m3 < body.analytic_volume_m3


def test_faceted_meshes_are_closed_and_outward_oriented() -> None:
    """Every faceted mesh satisfies the G1 closed-mesh contract."""
    model = reference_cad_model()
    assert len(model.faceted_meshes) == len(BODY_NAMES)
    for mesh in model.faceted_meshes:
        assert mesh.signed_volume_m3() > 0.0
        assert mesh.face_count > 0


def test_faceted_volumes_track_the_reference_mesh_within_the_polygon_bound() -> None:
    """Faceted and G1 volumes agree within the exact polygon-deficit bound."""
    model = reference_cad_model()
    reference = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        DEFAULT_REFERENCE_MESH_SEGMENTS,
    )
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.reference_mesh_volume_m3 == mesh.signed_volume_m3()
        assert body.mesh_volume_relative_difference >= 0.0
        assert body.mesh_volume_relative_difference <= body.mesh_volume_difference_bound


def test_bodies_touch_where_the_assembly_says_they_touch() -> None:
    """Device-level placement identities hold in the B-rep bounding boxes."""
    model = reference_cad_model()
    stations = axial_stations(reference_configuration(), reference_geometry())
    boxes = {
        body["name"]: (body["bounding_box_min_m"], body["bounding_box_max_m"])
        for body in model.assembly_manifest["bodies"]
    }
    vessel_low, vessel_high = boxes["central_cell_vessel"]
    coil_up_low, coil_up_high = boxes["mirror_coil_upstream"]
    coil_down_low, coil_down_high = boxes["mirror_coil_downstream"]
    tank_up_low, tank_up_high = boxes["expander_tank_upstream"]
    tank_down_low, tank_down_high = boxes["expander_tank_downstream"]
    _, wall_up_high = boxes["end_wall_upstream"]
    wall_down_low, _ = boxes["end_wall_downstream"]
    # the vessel meets both mirror coils face to face at the inboard faces
    assert math.isclose(vessel_low[2], coil_up_high[2], abs_tol=1.0e-9)
    assert math.isclose(vessel_high[2], coil_down_low[2], abs_tol=1.0e-9)
    # each tank starts at the outboard face of its coil
    assert math.isclose(tank_up_high[2], coil_up_low[2], abs_tol=1.0e-9)
    assert math.isclose(tank_down_low[2], coil_down_high[2], abs_tol=1.0e-9)
    # each end wall closes its tank
    assert math.isclose(wall_up_high[2], tank_up_low[2], abs_tol=1.0e-9)
    assert math.isclose(wall_down_low[2], tank_down_high[2], abs_tol=1.0e-9)
    # the coils are centred on the throats
    assert math.isclose(
        (coil_down_low[2] + coil_down_high[2]) / 2.0,
        stations.throat_m,
        abs_tol=1.0e-9,
    )


def test_the_revolved_column_passes_the_printed_bore() -> None:
    """The anchor flux tube is inside the printed aperture as a B-rep solid.

    The tessellated tube clearing the bore is the tier-G1 claim; this is
    the same statement about the exact solid the third-party kernel built,
    read off its own bounding box at the throat.
    """
    model = anchor_cad_model()
    tube = next(
        body
        for body in model.assembly_manifest["bodies"]
        if body["name"] == "plasma_flux_tube"
    )
    assert math.isclose(
        tube["bounding_box_min_m"][2], -ANCHOR_THROAT_POSITION_M, abs_tol=1.0e-9
    )
    assert math.isclose(
        tube["bounding_box_max_m"][2], ANCHOR_THROAT_POSITION_M, abs_tol=1.0e-9
    )
    assert math.isclose(
        tube["bounding_box_max_m"][0],
        ANCHOR_MIDPLANE_PLASMA_RADIUS_M,
        abs_tol=1.0e-9,
    )
    throat_sections = [
        item
        for item in model.clearances
        if item.bore_radius_m == ANCHOR_WARM_BORE_RADIUS_M
    ]
    assert len(throat_sections) == 2
    for item in throat_sections:
        assert item.clearance_m > 0.0


def test_step_export_is_byte_deterministic() -> None:
    """Two builds of the same design give byte-identical STEP documents."""
    first = build_device_cad(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
    )
    second = reference_cad_model()
    assert first.step_data == second.step_data
    assert first.step_sha256 == second.step_sha256
    assert len(first.step_sha256) == 64
    assert first.digest_sha256() == second.digest_sha256()


def test_step_round_trip_reproduces_the_volumes(tmp_path: Path) -> None:
    """Re-importing the written STEP gives the bodies' volumes within 1e-9.

    The re-import runs in a subprocess, which is how a consumer reads the
    file: a separate reader process.
    """
    model = reference_cad_model()
    target = tmp_path / "device.step"
    written = write_step(target, model)
    assert written == len(model.step_data)
    assert target.read_bytes() == model.step_data
    assert hashlib.sha256(target.read_bytes()).hexdigest() == model.step_sha256
    script = (
        "import json, sys;"
        "import cadquery;"
        "solids = cadquery.importers.importStep(sys.argv[1]).solids().vals();"
        "print(json.dumps(sorted(float(s.Volume()) for s in solids)))"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", script, str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    got = json.loads(completed.stdout)
    assert len(got) == len(BODY_NAMES)
    expected = sorted(body.analytic_volume_m3 for body in model.bodies)
    for value, reference in zip(got, expected, strict=True):
        assert math.isclose(value, reference, rel_tol=MEASURE_TOLERANCE)


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = reference_cad_model()
    record = model.to_record()
    assert record["schema"] == CAD_MODEL_SCHEMA
    assert record["schema_version"] == CAD_MODEL_SCHEMA_VERSION
    assert record["non_claims"] == list(CAD_MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["midplane_plasma_radius_m"] == REFERENCE_MIDPLANE_PLASMA_RADIUS_M
    assert record["field_profile"] == [
        list(sample) for sample in reference_field_profile()
    ]
    assert record["flux_tube_profile"] == [
        list(sample) for sample in model.tube_profile
    ]
    assert record["reference_mesh_segments"] == DEFAULT_REFERENCE_MESH_SEGMENTS
    assert record["linear_deflection_m"] == DEFAULT_LINEAR_DEFLECTION_M
    assert record["angular_deflection_rad"] == DEFAULT_ANGULAR_DEFLECTION_RAD
    assert record["backend_versions"]["cadquery"] != "unavailable"
    assert record["backend_versions"]["ocp"] != "unavailable"
    assert record["assembly_manifest"]["schema"] == MANIFEST_SCHEMA
    assert record["assembly_manifest"]["body_count"] == len(BODY_NAMES)
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_CAD_MODEL_SHA256


def test_invalid_segments_are_refused() -> None:
    """The reference mesh segment rule is enforced by the build."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
            reference_field_profile(),
            20,
        )


def test_aperture_violations_are_refused_by_the_cad_build() -> None:
    """The family's defining refusal holds at tier G2 as well as tier G1."""
    geometry = dataclasses.replace(
        reference_geometry(), mirror_coil_warm_bore_radius_m=0.02
    )
    with pytest.raises(DeviceGeometryError, match="mirror_coil_upstream"):
        build_device_cad(
            reference_configuration(),
            geometry,
            REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
            reference_field_profile(),
        )


def test_invalid_deflections_are_refused() -> None:
    """Non-positive deflections are refused by the build."""
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
            reference_field_profile(),
            linear_deflection_m=0.0,
        )


def test_body_evidence_refuses_out_of_bound_values() -> None:
    """The library's evidence record fails closed when a bound is violated.

    The per-body check belongs to the shared library (its ADR 0009), so a
    violated bound surfaces as the library's error type; a build re-raises
    it under the device error type, which the build refusal tests cover.
    """
    body = reference_cad_model().bodies[0]
    with pytest.raises(CadError, match="volume_relative_error"):
        dataclasses.replace(body, volume_relative_error=1.0)
    with pytest.raises(CadError, match="surface_area_relative_error"):
        dataclasses.replace(body, surface_area_relative_error=1.0)
    with pytest.raises(CadError, match="faceted_volume_relative_deficit"):
        dataclasses.replace(body, faceted_volume_relative_deficit=1.0)
    with pytest.raises(CadError, match="mesh_volume_relative_difference"):
        dataclasses.replace(body, mesh_volume_relative_difference=1.0)


def test_model_refuses_a_foreign_body_inventory() -> None:
    """A record with the wrong body order is refused."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        dataclasses.replace(model, bodies=model.bodies[::-1])


def test_model_refuses_invalid_declared_parameters() -> None:
    """The record refuses invalid segments, deflections and digests."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="multiple"):
        dataclasses.replace(model, reference_mesh_segments=20)
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        dataclasses.replace(model, linear_deflection_m=math.nan)
    with pytest.raises(DeviceGeometryError, match="angular_deflection_rad"):
        dataclasses.replace(model, angular_deflection_rad=-1.0)
    with pytest.raises(DeviceGeometryError, match="step_sha256"):
        dataclasses.replace(model, step_sha256="not-a-digest")
    with pytest.raises(DeviceGeometryError, match="assembly_manifest"):
        dataclasses.replace(model, assembly_manifest={"schema": "foreign"})
    manifest = dict(model.assembly_manifest)
    manifest["body_count"] = 1
    with pytest.raises(DeviceGeometryError, match="body_count"):
        dataclasses.replace(model, assembly_manifest=manifest)


def test_evidence_projection_is_json_serialisable() -> None:
    """The per-body evidence projects to JSON with every declared bound."""
    model = reference_cad_model()
    record = model.bodies[0].to_record()
    assert record["name"] == BODY_NAMES[0]
    assert record["volume_relative_error"] <= MEASURE_TOLERANCE
    assert (
        record["faceted_volume_relative_deficit"]
        <= record["faceted_volume_deficit_bound"]
    )
    json.dumps(record, allow_nan=False)
