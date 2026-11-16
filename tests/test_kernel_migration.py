# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — repaired geometry dependency integration

"""Exercise repaired mesh measures and export refusals through the device API.

The scaled designs are synthetic numerical cases, not physical models of
microscopic mirrors. Their role is to distinguish a representable float64
geometry from an export whose float32 positions collapse its facets.
"""

from __future__ import annotations

import dataclasses
import math

import pytest
from scpn_reactor_kernels.errors import GeometryError

from geometry_fixtures import (
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
)
from scpn_mirror_core.geometry import (
    DeviceGeometry,
    DeviceModel3D,
    build_device_model,
    glb_bytes,
    stl_bytes,
)


def scaled_device(scale: float) -> DeviceModel3D:
    """Build the public synthetic device with every length scaled equally.

    Parameters
    ----------
    scale
        Positive dimensionless factor applied to geometry, axial samples,
        central-cell length and midplane radius; field strengths stay fixed.

    Returns
    -------
    DeviceModel3D
        The complete ten-body model built through the consumer's public API.
    """
    configuration = reference_configuration()
    layout = dataclasses.replace(
        configuration.layout,
        central_cell_length_m=configuration.layout.central_cell_length_m * scale,
    )
    configuration = dataclasses.replace(configuration, layout=layout)
    geometry = DeviceGeometry(
        **{
            name: value * scale
            for name, value in reference_geometry().to_record().items()
        }
    )
    profile = tuple(
        (height * scale, strength) for height, strength in reference_field_profile()
    )
    return build_device_model(
        configuration,
        geometry,
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M * scale,
        profile,
        8,
    )


def test_representable_small_device_retains_volume_and_area() -> None:
    """A float64 design keeps its measures when intermediate squares underflow."""
    scale = 1.0e-100
    ordinary = scaled_device(1.0)
    small = scaled_device(scale)
    for source, mesh in zip(ordinary.meshes, small.meshes, strict=True):
        assert math.isfinite(mesh.signed_volume_m3())
        assert mesh.signed_volume_m3() > 0.0
        assert mesh.signed_volume_m3() / scale**3 == pytest.approx(
            source.signed_volume_m3(), rel=1.0e-12
        )
        assert mesh.surface_area_m2() / scale**2 == pytest.approx(
            source.surface_area_m2(), rel=1.0e-12
        )


def test_device_exports_refuse_facets_lost_in_float32() -> None:
    """Both public export paths refuse a valid mesh that float32 cannot store."""
    model = scaled_device(1.0e-50)
    with pytest.raises(GeometryError, match="float32"):
        stl_bytes(model.meshes)
    with pytest.raises(GeometryError, match="float32"):
        glb_bytes(model)


@pytest.mark.parametrize("offset", [100.0, -100.0, 1.0e8])
def test_device_body_volume_survives_coordinate_translation(offset: float) -> None:
    """Moving actual device meshes keeps volume within coordinate rounding."""
    model = scaled_device(1.0)
    # The smallest declared wall is 0.01 m. The bound is the library's
    # documented 3*ulp(offset)/L coordinate-rounding bound, not a loosened
    # tolerance for an unstable determinant sum.
    bound = 3.0 * math.ulp(offset) / 0.01
    for mesh in model.meshes:
        translated = dataclasses.replace(
            mesh,
            vertices=tuple(
                (x + offset, y + offset, z + offset) for x, y, z in mesh.vertices
            ),
        )
        original = mesh.signed_volume_m3()
        assert abs(translated.signed_volume_m3() - original) / original <= bound
