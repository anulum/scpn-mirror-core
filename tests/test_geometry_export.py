# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — open-format export tests

"""Binary STL and GLB layouts read back with minimal spec-level readers.

The serialisers are the pinned library's kernels; these tests prove the
device-side contract — that the provenance extras carry the declared
field profile the flux tube rests on, that the export delegates rather
than reimplements, and that the container layout reads back byte for
byte. All values are synthetic.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import pytest
from scpn_reactor_kernels import geometry as library

from geometry_fixtures import (
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    reference_configuration,
    reference_field_profile,
    reference_geometry,
)
from scpn_mirror_core.geometry import (
    BODY_NAMES,
    GLTF_GENERATOR,
    MODEL_SCHEMA,
    STL_HEADER,
    DeviceModel3D,
    build_device_model,
    glb_bytes,
    glb_extras,
    stl_bytes,
    write_glb,
    write_stl,
)


def reference_model(segments: int = 8) -> DeviceModel3D:
    """Build the reference model of these tests at a segment count."""
    return build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        reference_field_profile(),
        segments,
    )


def read_glb(data: bytes) -> tuple[dict[str, Any], bytes]:
    """Parse a GLB container per the glTF 2.0 binary layout."""
    magic, version, total = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67
    assert version == 2
    assert total == len(data)
    json_length, json_type = struct.unpack_from("<II", data, 12)
    assert json_type == 0x4E4F534A
    assert json_length % 4 == 0
    document = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    offset = 20 + json_length
    bin_length, bin_type = struct.unpack_from("<II", data, offset)
    assert bin_type == 0x004E4942
    assert bin_length % 4 == 0
    binary = data[offset + 8 : offset + 8 + bin_length]
    assert offset + 8 + bin_length == total
    return document, binary


@pytest.mark.parametrize("segments", [8, 16, 24, 32])
def test_glb_layout_nodes_and_accessors(segments: int) -> None:
    """Every body is one named node with aligned position and index accessors."""
    model = reference_model(segments)
    document, binary = read_glb(glb_bytes(model))
    assert document["asset"] == {"version": "2.0", "generator": GLTF_GENERATOR}
    assert document["scenes"] == [{"nodes": list(range(len(BODY_NAMES)))}]
    assert [node["name"] for node in document["nodes"]] == list(BODY_NAMES)
    assert document["buffers"][0]["byteLength"] <= len(binary)
    extras = document["extras"]
    assert extras["schema"] == MODEL_SCHEMA
    assert extras["model_sha256"] == model.digest_sha256()
    assert extras["segments"] == segments
    assert extras["midplane_plasma_radius_m"] == REFERENCE_MIDPLANE_PLASMA_RADIUS_M
    assert extras["units"]["length"] == "metre"
    assert extras["units"]["magnetic_flux_density"] == "tesla"
    for index, mesh in enumerate(model.meshes):
        node = document["nodes"][index]
        assert node["mesh"] == index
        assert node["extras"]["mesh_sha256"] == mesh.digest_sha256()
        primitive = document["meshes"][index]["primitives"][0]
        assert primitive["mode"] == 4
        positions = document["accessors"][primitive["attributes"]["POSITION"]]
        indices = document["accessors"][primitive["indices"]]
        assert positions["count"] == mesh.vertex_count
        assert positions["type"] == "VEC3"
        assert indices["count"] == 3 * mesh.face_count
        assert indices["componentType"] == 5125
        view = document["bufferViews"][positions["bufferView"]]
        assert view["byteOffset"] % 4 == 0
        assert view["byteLength"] == 12 * mesh.vertex_count
        first = struct.unpack_from("<3f", binary, view["byteOffset"])
        expected = struct.unpack("<3f", struct.pack("<3f", *mesh.vertices[0]))
        assert first == expected
        index_view = document["bufferViews"][indices["bufferView"]]
        stream = struct.unpack_from(
            f"<{3 * mesh.face_count}I", binary, index_view["byteOffset"]
        )
        assert stream[:3] == mesh.faces[0]


def test_the_extras_carry_the_declared_field_the_column_rests_on() -> None:
    """A viewer can see which declared field produced the flux tube."""
    model = reference_model()
    extras = glb_extras(model)
    assert extras["field_profile"] == [
        list(sample) for sample in reference_field_profile()
    ]
    assert extras["flux_tube_profile"] == [
        list(sample) for sample in model.tube_profile
    ]
    assert extras["flux_tube_clearances"] == [
        item.to_record() for item in model.clearances
    ]


def test_exports_delegate_to_the_library_kernels_with_device_provenance() -> None:
    """The bytes are the library's, with exactly the model's provenance as extras."""
    model = reference_model()
    record = model.to_record()
    extras = glb_extras(model)
    assert extras == {
        "schema": MODEL_SCHEMA,
        "schema_version": "1.0.0",
        "configuration_digest_sha256": model.configuration_digest_sha256,
        "geometry_digest_sha256": model.geometry_digest_sha256,
        "model_sha256": model.digest_sha256(),
        "midplane_plasma_radius_m": REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        "field_profile": record["field_profile"],
        "flux_tube_profile": record["flux_tube_profile"],
        "flux_tube_clearances": record["flux_tube_clearances"],
        "segments": 8,
        "units": record["units"],
        "non_claims": record["non_claims"],
    }
    assert glb_bytes(model) == library.glb_bytes(model.meshes, extras)
    assert stl_bytes(model.meshes) == library.stl_bytes(model.meshes)
    assert STL_HEADER is library.STL_HEADER
    assert GLTF_GENERATOR is library.GLTF_GENERATOR
    document, _ = read_glb(glb_bytes(model))
    assert document["extras"] == extras


def test_glb_is_deterministic() -> None:
    """The same model yields identical bytes."""
    model = reference_model()
    assert glb_bytes(model) == glb_bytes(model)


def test_stl_layout() -> None:
    """The binary STL carries every face with a unit normal and zero attribute."""
    model = reference_model()
    data = stl_bytes(model.meshes)
    assert data[:80] == STL_HEADER
    assert not data.startswith(b"solid")
    count = struct.unpack_from("<I", data, 80)[0]
    assert count == sum(mesh.face_count for mesh in model.meshes)
    assert len(data) == 84 + 50 * count
    offset = 84
    for mesh in model.meshes:
        for face in mesh.faces:
            normal = struct.unpack_from("<3f", data, offset)
            length = sum(component * component for component in normal)
            assert abs(length - 1.0) <= 1.0e-6
            vertices = struct.unpack_from("<9f", data, offset + 12)
            expected = struct.unpack(
                "<9f",
                struct.pack(
                    "<9f", *(c for corner in face for c in mesh.vertices[corner])
                ),
            )
            assert vertices == expected
            assert struct.unpack_from("<H", data, offset + 48)[0] == 0
            offset += 50


def test_writers_create_files(tmp_path: Path) -> None:
    """The file writers persist exactly the serialised bytes."""
    model = reference_model()
    stl_path = tmp_path / "device.stl"
    glb_path = tmp_path / "device.glb"
    assert write_stl(stl_path, model.meshes) == len(stl_bytes(model.meshes))
    assert write_glb(glb_path, model) == len(glb_bytes(model))
    assert stl_path.read_bytes() == stl_bytes(model.meshes)
    assert glb_path.read_bytes() == glb_bytes(model)
