<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ADR 0008
-->

# ADR 0008 — Device CAD model: B-rep solids and a deterministic STEP export

Status: accepted (2026-09-03). Adds the fifth implemented capability,
`device_cad_model`, at `computational_prototype`. Companion of ADR 0007.

## Context

The tier-G1 model (ADR 0007) is a tessellation: closed, deterministic,
exact in its own terms, and an approximation of the surfaces it stands
for. Downstream engineering work — meshing for a field or a thermal
solve, interference checks, a drawing — wants exact surfaces and an
interchange format. That means a boundary-representation kernel, and a
B-rep kernel is a large third-party dependency this repository must not
require in order to run.

The family adds one requirement the earlier tiers did not have. Its
plasma body is a surface of revolution through a sampled radius profile,
so the CAD tier has to revolve the same profile the tessellation is built
from, or the two tiers would describe two similar bodies rather than one.

## Decision

1. The CAD model is a **second tier of the same capability domain**, not a
   new domain: the same ten bodies of ADR 0007, the same names, roles,
   materials and order, built as exact B-rep solids.
2. **The CAD back-end is an optional extra, per package.** The base
   dependency is the plain library pin; `[project.optional-dependencies]
   cad` names the same commit with the library's own `cad` extra. The
   device configuration, the diagnostics, the level-0 physics and the
   tier-G1 model all work without a B-rep kernel, so declaring one a hard
   dependency would state something untrue about this package and would
   pull a roughly one-gigabyte back-end into every environment that
   installs it. Exactly two CI jobs install the extra — the coverage job,
   because the CAD module is covered like any other, and the `cad` job —
   and both install the system library the mesher links against first.
3. The B-rep bodies, the STEP writer, the faceting and the per-body
   evidence are consumed from the pinned shared kernel library
   (`cad_brep_solids`, `cad_profiles`, `cad_step_export`, `cad_faceting`,
   `cad_evidence`). The flux tube is revolved through the same
   `(z, radius)` profile the tier-G1 mesh is tessellated from, and a test
   asserts the two tiers carry the identical profile, field profile and
   clearances.
4. **OpenCASCADE is not the bit-exact floor.** Every body is checked
   fail-closed against its analytic closed form within the library's
   declared relative tolerance `1e-9`. For nine bodies that closed form is
   the elementary tube or disc; for the flux tube it is the exact
   frustum-stack sum of its linear profile — exact rather than
   approximate, because the profile contract is linear between samples.
   The faceted volume is checked against the declared chord-deficit bound
   of the mesher's linear deflection and against the tier-G1 mesh at the
   declared reference segment count within the exact polygon-deficit
   bound.
5. The aperture refusal of ADR 0007 holds at this tier too: the CAD build
   runs the same tier-G1 build first, so a design whose column does not
   clear a bore is refused before any solid is revolved.
6. STEP bytes are written by the library's normalised deterministic
   writer and the record carries their SHA-256. Determinism is claimed
   **within one pinned back-end environment only**; a back-end bump
   re-pins the reference digests as a governed data change.
7. The canonical record carries the schema identity, the units and axis
   convention, both source digests, the declared midplane radius, the
   declared field profile, the flux-tube profile, the aperture
   clearances, the declared deflections and reference segment count, the
   back-end versions, the assembly manifest, the STEP digest and the
   per-body evidence; its SHA-256 identifies the exact model.

## Consequences

The repository can hand a downstream tool exact solids and a STEP file
whose bytes are reproducible in the pinned environment, without making a
B-rep kernel a condition of installing it. The two tiers are provably one
design: same bodies, same profile, same clearances, checked against the
same closed forms. Nothing here carries a material property, a load, a
field or a neutronic quantity, and no value describes a real machine.
