<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — Device 3D model contract
-->

# Device 3D model contract

Producer-owned contract of the `device_3d_model` and `device_cad_model`
capabilities (`computational_prototype`; design records ADR 0006, ADR 0007
and ADR 0008). It states exactly what the exported files contain so that a
consumer — the portfolio presentation layer, an engineering tool, a
reviewer — can read them without importing this package. Nothing in the
files or in this contract creates a federation, a claim, or an engineering
statement.

## Records

| Record | Schema | Identity |
|---|---|---|
| Device configuration | package `DeviceConfiguration` record | `configuration_digest_sha256` |
| Device geometry | package `DeviceGeometry` record (thirteen SI fields) | `geometry_digest_sha256` |
| Device model | `scpn.mirror-3d-model.v1` version `1.0.0` | `model_sha256` = SHA-256 of the canonical model record |
| Body mesh | little-endian `uint32 vertex_count, uint32 face_count, float64 x y z per vertex, uint32 i j k per face` | `mesh_sha256` |

The model record carries: `schema`, `schema_version`, `units`,
`non_claims`, `configuration_digest_sha256`, `geometry_digest_sha256`,
`midplane_plasma_radius_m`, `field_profile`, `flux_tube_profile`,
`flux_tube_clearances`, `segments`, and `bodies` (one summary per body:
`name`, `role`, `material_identifier`, `vertex_count`, `face_count`,
`volume_m3`, `surface_area_m2`, `bounding_box_min_m`,
`bounding_box_max_m`, `mesh_sha256`). Canonical bytes are UTF-8 JSON with
sorted keys, minimal separators and a trailing newline; NaN and infinity
are never emitted.

`field_profile` is the DECLARED axial field, as `[z_m, b_t]` pairs in
ascending `z`. `flux_tube_profile` is the `[z_m, radius_m]` profile it
implies under flux conservation. `flux_tube_clearances` carries, per
axial section the column enters, `section`, `bore_radius_m`,
`largest_flux_tube_radius_m` and `clearance_m`.

## Units and axes

- Length unit: metre; magnetic flux density: tesla. In every record and
  in both mesh export formats lengths are metres.
- Right-handed Cartesian frame; `z` is the device axis, increasing
  downstream; **the origin is the central-cell midplane on the axis**. The
  assembly is symmetric about `z = 0`: the upstream half occupies negative
  `z`.
- Float64 in the records and the canonical mesh bytes; float32 in STL and
  GLB because both containers require it (the canonical digests are taken
  on the float64 bytes, never on the exports).

## The one relation this tier applies

The plasma body is a **flux tube**, not a body of constant radius.
Conservation of magnetic flux through the column gives

    r(z) = r_mid sqrt(B_mid / B(z))

and that is the whole physical content of the geometry tier. `B(z)` is
declared by the caller as ordered samples, never solved or fitted here;
`B_mid` is the sample at `z = 0`, the plane the declared midplane radius
belongs to. Between two samples the surface is a straight line in radius —
a stack of conical frusta — so the closed forms of its volume and lateral
area are exact and the tessellation is the approximation, not the reverse.

## Bodies (fixed order, fixed names)

`L` is the configuration's central-cell length (throat to throat), so the
throats sit at `±L/2`; `L_m` is the mirror-coil axial length, `L_t` the
tank length, `t_w` the end-wall thickness, `d` the central-cell coil
offset and `L_d` its axial length. `v = L/2 - L_m/2` is a coil's inboard
face, `c = L/2 + L_m/2` its outboard face, `e = c + L_t` a tank's outboard
face and `w = e + t_w` the end of the assembly.

| Node name | Role | Material token | Analytic body |
|---|---|---|---|
| `central_cell_vessel` | `vacuum_boundary` | `vessel_wall` | annular tube, bore to bore+wall, `z in [-v, v]` |
| `central_cell_coil_upstream` | `coil` | `coil_conductor` | annular tube, bore to bore+winding, `z in [-(d + L_d/2), -(d - L_d/2)]` |
| `central_cell_coil_downstream` | `coil` | `coil_conductor` | annular tube, bore to bore+winding, `z in [d - L_d/2, d + L_d/2]` |
| `mirror_coil_upstream` | `coil` | `coil_conductor` | annular tube, warm bore to warm bore+winding, `z in [-c, -v]` |
| `mirror_coil_downstream` | `coil` | `coil_conductor` | annular tube, warm bore to warm bore+winding, `z in [v, c]` |
| `expander_tank_upstream` | `vacuum_boundary` | `vessel_wall` | annular tube, bore to bore+wall, `z in [-e, -c]` |
| `expander_tank_downstream` | `vacuum_boundary` | `vessel_wall` | annular tube, bore to bore+wall, `z in [c, e]` |
| `end_wall_upstream` | `vacuum_boundary` | `end_wall` | solid cylinder of the tank outer radius, `z in [-w, -e]` |
| `end_wall_downstream` | `vacuum_boundary` | `end_wall` | solid cylinder of the tank outer radius, `z in [e, w]` |
| `plasma_flux_tube` | `plasma` | `plasma` | surface of revolution through `flux_tube_profile`, closed with end discs |

Material tokens are declarations only; no density, composition,
conductivity or nuclear property is carried anywhere.

Every body is a closed triangle surface with outward orientation
(counter-clockwise vertex order seen from outside), no degenerate face,
every directed edge appearing exactly once together with its reverse.
Segment counts are multiples of eight (at least eight).

## Aperture clearance

A mirror is the one family here whose plasma boundary must pass through
an aperture narrower than itself. The model states, per axial section —
upstream tank, upstream throat, central cell, downstream throat,
downstream tank — the largest flux-tube radius anywhere inside it and the
bore it clears, and **refuses to build a design in which the column is as
wide as that bore or wider**, naming the section. The largest radius is
exact rather than sampled: the profile is linear in radius between
samples, so the maximum on a sub-interval is the larger of its two
interpolated endpoints.

## Files

- **Binary STL** (`stl_bytes`, `write_stl`): 80-byte header written by the
  shared library kernel, `uint32` triangle count, then per triangle a
  float32 unit normal, three float32 vertices and a zero `uint16`
  attribute. All bodies are concatenated in the fixed order; STL carries
  no names, so the GLB is the file for body identity.
- **glTF 2.0 binary** (`glb_bytes`, `write_glb`): header (magic `glTF`,
  version 2, total length), one JSON chunk (space-padded to four bytes),
  one binary chunk (zero-padded). One `mesh` and one `node` per body, the
  node named as in the table above, with `node.extras` = `{role,
  material_identifier, mesh_sha256}`. Each primitive has a float32 `VEC3`
  `POSITION` accessor with `min`/`max` and a `uint32` `SCALAR` index
  accessor, mode `TRIANGLES`; buffer views are four-byte aligned. The
  document `extras` carry `schema`, `schema_version`,
  `configuration_digest_sha256`, `geometry_digest_sha256`, `model_sha256`,
  `midplane_plasma_radius_m`, `field_profile`, `flux_tube_profile`,
  `flux_tube_clearances`, `segments`, `units` and `non_claims`. No
  materials, textures, animations or extensions are used.
- **STEP** (`write_step`, capability `device_cad_model`, ADR 0008): an ISO
  10303-21 (AP214) export of the B-rep assembly of the SAME ten bodies,
  built by the pinned OpenCASCADE kernel through the shared library's
  `cad` group; the flux tube is revolved through the same
  `flux_tube_profile` the tessellation is built from. The header is
  normalised by the library: the `FILE_NAME` name and time stamp are fixed
  literals, the assembly usage-occurrence identifiers are renumbered from
  one, the writer's continuation lines are unfolded, and
  `FILE_DESCRIPTION` carries the generator name and the provenance extras
  (record schema, both source digests, the assembly manifest digest, the
  back-end versions, the units and the non-claims) as a JSON string. The
  file written is exactly the byte string whose SHA-256 the CAD model
  record carries as `step_sha256`, next to the back-end versions; the
  bytes are deterministic within one pinned back-end environment and no
  identity across OpenCASCADE versions is claimed. The CAD model record
  (`scpn.mirror-cad-model.v1` version `1.0.0`) additionally carries, per
  body, the B-rep volume and area against the analytic closed form within
  `1e-9` relative — for the flux tube that closed form is the exact
  frustum-stack sum of its profile — the faceted volume deficit within the
  declared bound `2 d / r`, and the faceted volume against the tier-G1
  mesh at the declared reference segment count within the exact
  polygon-deficit bound. Bounding boxes in the assembly manifest are the
  exact boxes of the geometry: they do not depend on whether the bodies
  have been faceted.

## Determinism

The same configuration, geometry, midplane radius, field profile and
segment count always yield the same records, the same mesh bytes and the
same export bytes, on every backend: the vertex coordinates are computed
by the polynomial unit circle of the shared kernel library
`scpn-reactor-kernels` (pinned by commit object and kernel-inventory
digest in `reactor-domain.json`, `kernel_library`) with fixed operation
order, proven bit-exact between that library's Python floor and its native
kernels, and this device model is proven bit-exact against the library's
native module body by body — the profiled flux tube included. The
serialisers are the library's kernel `geometry_exports`: the binary STL
header and the glTF `asset.generator` name that kernel, while the document
`extras` carry this repository's provenance. A change of the library pin
is a governed data change of this repository.

## Simplifications

The end walls are plain closing discs of the tank outer diameter; pumping
ducts, limiters, end rings, gas valves, heating hardware, struts,
cryostats, seals, ports, diagnostics and supports are not modelled. The
coils are annular winding envelopes with no conductor layout: their field
shaping lives in the declared field profile and in the level-0 models, not
in this geometry.

## Non-claims

- The bodies are analytic surfaces (tier G1) or B-rep solids (tier G2) of
  a declared design: no equilibrium boundary, no engineering model. The
  plasma body is the surface of revolution of a DECLARED field profile
  under one conservation relation, not a computed plasma boundary and not
  an anisotropic-pressure solution.
- The field profile resolves no local structure between the samples it is
  given, and a coarser profile is a different body rather than a bound on
  a finer one.
- No material property, load, field or neutronic quantity is carried.
- No value describes or validates any real machine; a dimension
  reproduced from a published arrangement is an anchor, not a claim about
  that machine.
- Providing these files does not federate the repository, present it, or
  gate its execution anywhere; those remain the portfolio layer's domain.
