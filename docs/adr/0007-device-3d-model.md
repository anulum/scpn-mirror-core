<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ADR 0007
-->

# ADR 0007 — Device 3D model: a flux tube, not a cylinder

Status: accepted (2026-09-03). Adds the fourth implemented capability,
`device_3d_model`, at `computational_prototype`.

## Context

The device repository owns device geometry (ADR 0001 boundary: plant and
experiment truth, configuration policy). Until this record the repository
carried the axial field and the cell layout as numbers only; there was no
mechanical envelope and no way to present, measure or hand a design to
downstream tooling.

The five device families that landed this tier before this one are built
from bodies of constant radius: cylinders and annular tubes. **A magnetic
mirror cannot be.** Its confined plasma is a flux tube, and conservation
of magnetic flux through the column ties its radius to the field along
the axis,

    r(z) = r_mid sqrt(B_mid / B(z)),

so the column is widest at the midplane and narrowest at the throats by a
factor `sqrt(R_m)`, where `R_m = B_max / B_min` is the mirror ratio the
configuration already validates as the family's defining property.

This is not a modelling preference, and the filed source settles it
arithmetically rather than by taste. D. Endrizzi et al., "Physics basis
for the Wisconsin HTS Axisymmetric Mirror (WHAM)", J. Plasma Phys. 89
(2023) 975890501 (CC BY 4.0), prints in sections 2 and 2.1 a target
plasma of radius `a = 0.1 m` and `17 T`, `5.5 cm` warm bore mirror
magnets centred at `z = ±98 cm`, with the central field raised to a
maximum of `0.86 T`. A body of constant radius `0.1 m` does not pass
through a bore of radius `0.0275 m` at all. The flux tube does: at
`R_m = 17 / 0.86` the midplane radius narrows to `0.1 / sqrt(R_m) ≈
0.0225 m` at the throat, which clears the printed aperture. Drawing this
family's plasma as a cylinder would not be a coarse approximation; it
would be a body that cannot exist inside the machine whose dimensions the
source prints.

## Decision

1. A new owned domain `device_geometry_and_3d_model` is declared in
   `reactor-domain.json`: device-owned geometry parameters and the 3D
   model derived from them. It is disjoint from solver mathematics (no
   equation is solved), from portfolio presentation (the exported files
   are an offer, `docs/DEVICE_3D_MODEL_CONTRACT.md`) and from any
   engineering lane (no property is carried).
2. `DeviceGeometry` (`src/scpn_mirror_core/geometry/device.py`) carries
   the mechanical envelope only: the central-cell vessel bore and wall,
   the central-cell coil offset, bore, winding thickness and axial
   length, the mirror-coil warm bore, winding thickness and axial length,
   the expansion-tank bore, wall and length, and the end-wall thickness.
   Thirteen declared fields, each strictly positive, with two envelope
   relations refused in the direction they are wrong: a central-cell coil
   may not sit inside the vessel wall it is wound around, and a tank that
   does not open out beyond the throat is not an expander.
3. **The mirror-coil positions are not declared here.** Each mirror coil
   is centred on a throat at `±central_cell_length_m / 2`, read from the
   validated configuration's `CellLayout`. One number, one home. The
   assembly is symmetric about the midplane, so `AxialStations` names the
   stations once on the positive side and the model mirrors them.
4. **The axial field profile is a declared quantity passed into the
   build, never invented by the geometry.** The caller supplies ordered
   `(z, B)` samples; `scpn_mirror_core.geometry.profile` validates them,
   cross-checks them against the configuration and converts them into the
   `(z, radius)` profile the library's `geometry_profiles` kernel takes.
   The geometry therefore states, and is tested on, exactly one physical
   relation — flux conservation — and solves no field. Between two samples
   the library's contract is a straight line; a caller who wants a finer
   surface passes finer samples, and the record says so.
5. Four fail-closed cross-checks against the configuration: the sample at
   `z = 0` must carry the configuration's `b_min_t`; the largest sample
   must carry its `b_max_t`; every sample carrying that largest field must
   lie inside a mirror coil, because a field maximum away from a throat is
   not a throat; and the profile must cover both throats without reaching
   past the vacuum envelope into an end wall.
6. **The aperture check is the family's defining refusal.** The model
   states, per axial section (tank, throat, central cell, throat, tank),
   the largest flux-tube radius anywhere inside that section and the bore
   it has to clear, and refuses a design where the column is as wide as
   the bore or wider, naming the section. The largest radius is exact, not
   sampled: the profile is linear in radius between samples, so the
   maximum on a sub-interval is the larger of its two interpolated
   endpoints, and the two sample heights are returned exactly rather than
   through the interpolation.
7. Ten bodies in a fixed order — `central_cell_vessel`,
   `central_cell_coil_upstream`, `central_cell_coil_downstream`,
   `mirror_coil_upstream`, `mirror_coil_downstream`,
   `expander_tank_upstream`, `expander_tank_downstream`,
   `end_wall_upstream`, `end_wall_downstream`, `plasma_flux_tube` — each
   a closed, outward-oriented triangle mesh regenerated deterministically
   from the two validated records, the declared midplane radius and the
   declared field profile.
8. The unit circle, the primitives, the profiled surface of revolution,
   the closed-mesh contract and the serialisers are consumed from the
   pinned shared kernel library (ADR 0006 here; the library's ADR 0007
   and ADR 0010 there). This repository re-implements no geometry.
9. The canonical record carries the schema identity, the units and axis
   convention, both source digests, the declared midplane radius, the
   declared field profile, the flux-tube profile it implies, the aperture
   clearances, the segment count, a summary of every body and fixed
   non-claims; its SHA-256 identifies the exact model.

## Why the midplane coil pair is in the inventory

The plan this record implements listed eight bodies. Ten shipped. The
source prints a second coil pair at `z = ±20 cm` that raises the central
field, and a printed dimension with no body to appear in is a fidelity
gap rather than a simplification: a mirror whose model carries no
central-cell coil implies a central field produced by nothing. The pair
is generic to the family — GDT and WHAM both have one — so it is a body
of the model, not a property of one anchor.

## Simplifications recorded on purpose

The end walls are closing discs of the tank outer radius; pumping ducts,
limiters, end rings, heating hardware, struts, cryostats and conductor
layouts are not modelled. The coils are annular winding envelopes and
carry no current and no force. The flux tube is the surface of revolution
of a declared field profile under one conservation relation: not an
equilibrium boundary, not an anisotropic-pressure solution, and not a
prediction of any machine. The field profile resolves no local structure
between the samples it is given.

## Consequences

The tier is a substrate for later engineering lanes and for presentation,
and it is the first tier in the group whose plasma body is not a body of
constant radius. Every fixture is synthetic except one anchor set built
from the printed values above, with the fields the source does not print
declared and marked as declared — the axial profile between the printed
endpoints included. Reproducing a printed dimension is an anchor, never a
claim about that machine.
