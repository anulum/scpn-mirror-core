# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device model parity against the library's native kernels

"""Bit-exact parity of the device model against the pinned library's native kernels.

The device model is composed on the Python floor of the shared kernel
library; this file proves that every body it builds — the profiled flux
tube included — agrees bit for bit with the library's native
tessellation and mesh measures, so the consumer inherits the library's
parity rather than re-proving the kernels. Skipped hermetically when the
library's optional native module is absent; when present, every vertex
coordinate, face index and measure is compared by float64 bit pattern,
never by tolerance. All inputs are synthetic.
"""

from __future__ import annotations

import pytest

from geometry_fixtures import (
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    bits,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
    stream_bits,
)
from scpn_mirror_core.geometry import axial_stations, build_device_model

native = pytest.importorskip("scpn_reactor_kernels_native")


def native_bodies(segments: int) -> list[tuple[list[float], list[int]]]:
    """Tessellate the ten device bodies through the library's native kernels."""
    geometry = reference_geometry()
    stations = axial_stations(reference_configuration(), geometry)
    model = build_device_model(
        reference_configuration(),
        geometry,
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        segments,
    )
    flat_profile = [value for sample in model.tube_profile for value in sample]
    streams = (
        native.tessellate_annular_tube(
            geometry.central_cell_vessel_bore_radius_m,
            geometry.central_cell_vessel_outer_radius_m,
            -stations.vessel_end_m,
            stations.vessel_end_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.central_cell_coil_bore_radius_m,
            geometry.central_cell_coil_outer_radius_m,
            -stations.central_cell_coil_high_m,
            -stations.central_cell_coil_low_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.central_cell_coil_bore_radius_m,
            geometry.central_cell_coil_outer_radius_m,
            stations.central_cell_coil_low_m,
            stations.central_cell_coil_high_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.mirror_coil_warm_bore_radius_m,
            geometry.mirror_coil_outer_radius_m,
            -stations.coil_end_m,
            -stations.vessel_end_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.mirror_coil_warm_bore_radius_m,
            geometry.mirror_coil_outer_radius_m,
            stations.vessel_end_m,
            stations.coil_end_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.expander_tank_bore_radius_m,
            geometry.expander_tank_outer_radius_m,
            -stations.expander_end_m,
            -stations.coil_end_m,
            segments,
        ),
        native.tessellate_annular_tube(
            geometry.expander_tank_bore_radius_m,
            geometry.expander_tank_outer_radius_m,
            stations.coil_end_m,
            stations.expander_end_m,
            segments,
        ),
        native.tessellate_cylinder(
            geometry.expander_tank_outer_radius_m,
            -stations.end_wall_end_m,
            -stations.expander_end_m,
            segments,
        ),
        native.tessellate_cylinder(
            geometry.expander_tank_outer_radius_m,
            stations.expander_end_m,
            stations.end_wall_end_m,
            segments,
        ),
        native.tessellate_profiled_solid(flat_profile, segments),
    )
    return [(list(vertices), list(faces)) for vertices, faces in streams]


@pytest.mark.parametrize("segments", [8, 32, 64])
def test_every_body_is_bit_exact_with_the_library_native_kernels(
    segments: int,
) -> None:
    """Vertices, faces, volume and area of all ten bodies agree bit for bit."""
    model = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        segments,
    )
    bodies = native_bodies(segments)
    for mesh, (vertices, faces) in zip(model.meshes, bodies, strict=True):
        floor = [component for vertex in mesh.vertices for component in vertex]
        assert stream_bits(floor) == stream_bits(vertices), mesh.name
        assert [index for face in mesh.faces for index in face] == faces, mesh.name
        volume = native.mesh_volume(vertices, faces)
        assert bits(volume) == bits(mesh.signed_volume_m3()), mesh.name
        assert bits(native.mesh_area(vertices, faces)) == bits(
            mesh.surface_area_m2()
        ), mesh.name


def test_the_flux_tube_closed_forms_are_bit_exact_with_the_native_kernel() -> None:
    """The exact frustum-stack volume and lateral area agree bit for bit.

    The tier-G2 evidence checks the third-party B-rep kernel against these
    closed forms, so the closed forms themselves are worth proving on both
    floors rather than on one.
    """
    model = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        8,
    )
    from scpn_reactor_kernels.geometry import (
        profile_lateral_area_m2,
        profile_volume_m3,
    )

    flat_profile = [value for sample in model.tube_profile for value in sample]
    assert bits(native.profile_volume(flat_profile)) == bits(
        profile_volume_m3(model.tube_profile)
    )
    assert bits(native.profile_lateral_area(flat_profile)) == bits(
        profile_lateral_area_m2(model.tube_profile)
    )
