# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device geometry, 3D model and CAD model

"""Device geometry, tier-G1 3D model and tier-G2 CAD model of the family.

A validated device geometry, the declared axial field profile and the one
relation applied to it, the composed device model record of ten analytic
bodies, the composed device CAD model record of the same ten bodies as
B-rep solids on the pinned third-party OpenCASCADE kernel, and the
device-side provenance of the open-format exports (binary STL, glTF 2.0
binary, STEP).

The unit circle, the tessellation primitives, the profiled surface of
revolution, the closed-mesh contract, the serialisers and the B-rep,
STEP, faceting and body-evidence kernels are consumed from the pinned
shared kernel library ``scpn_reactor_kernels``; the mesh type of every
body is that library's ``TriangleMesh``, the flux-tube profile is its
``Profile`` and the per-body evidence is its ``BodyEvidence``. Every
tier-G1 body is an analytic surface and every tier-G2 body is a B-rep
solid of the same declared design; nothing here is an equilibrium
boundary or an engineering model, and no value describes a real machine.
Design records: ADR 0007, ADR 0008.
"""

from __future__ import annotations

from scpn_mirror_core.geometry.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModelCAD,
    brep_bodies,
    build_device_cad,
)
from scpn_mirror_core.geometry.device import (
    GEOMETRY_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)
from scpn_mirror_core.geometry.export import (
    GLTF_GENERATOR,
    STL_HEADER,
    glb_bytes,
    glb_extras,
    stl_bytes,
    write_glb,
    write_step,
    write_stl,
)
from scpn_mirror_core.geometry.model import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    AxialStations,
    DeviceModel3D,
    aperture_sections,
    axial_stations,
    build_device_model,
)
from scpn_mirror_core.geometry.profile import (
    FIELD_MATCH_RELATIVE_TOLERANCE,
    MIN_FIELD_SAMPLES,
    ApertureSection,
    FieldProfile,
    FieldSample,
    FluxTubeClearance,
    flux_tube_clearances,
    flux_tube_profile,
    midplane_field_t,
    require_field_profile,
    throat_field_t,
)

__all__ = [
    "BODY_NAMES",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "FIELD_MATCH_RELATIVE_TOLERANCE",
    "GEOMETRY_FIELDS",
    "GLTF_GENERATOR",
    "MIN_FIELD_SAMPLES",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "STL_HEADER",
    "ApertureSection",
    "AxialStations",
    "DeviceGeometry",
    "DeviceModel3D",
    "DeviceModelCAD",
    "FieldProfile",
    "FieldSample",
    "FluxTubeClearance",
    "aperture_sections",
    "axial_stations",
    "brep_bodies",
    "build_device_cad",
    "build_device_model",
    "flux_tube_clearances",
    "flux_tube_profile",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "midplane_field_t",
    "require_field_profile",
    "stl_bytes",
    "throat_field_t",
    "write_glb",
    "write_step",
    "write_stl",
]
