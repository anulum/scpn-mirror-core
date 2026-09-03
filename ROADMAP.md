<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ROADMAP
-->

# Roadmap

Planned work and implemented capability are kept strictly separate. Anything
listed under "Planned" carries no implementation, no code, and no claim in
this repository until it appears in the capability inventory with evidence.

## Implemented (repository infrastructure, not reactor capability)

- Domain manifest (`reactor-domain.json`) with validator.
- Derived Studio portfolio descriptor (`not_federated`) with drift check.
- Generated capability inventory (truthfully empty) with drift check.
- CONTROL adapter specification (contract only, no implementation).
- Local and workflow gate definitions (lint, typing, tests, coverage,
  REUSE, security audit, SBOM, documentation checks).

- **Device configuration model** (landed 2026-08-31) — validated
  mirror-field and cell-layout objects for `gas_dynamic_mirror`,
  `simple_magnetic_mirror`, and `tandem_mirror` with hard plug-count and
  collisionality class invariants, the loss-cone fraction relation, a
  gas-dynamic mirror-ratio advisory, canonical digests, and the SPO
  registry data pin; `computational_prototype` (ADR 0002,
  `VALIDATION.md#device-configuration-model`). Plugging schemes and
  heating/beam inventory remain future work under the same capability.
- **Diagnostic and clock semantics** (landed 2026-08-31) — synthetic
  diagnostic-channel and clock declarations aligned fail-closed with the
  pinned SPO observability-profile catalogue (release `1.0.0`): candidate
  applicability, carrier admissibility, exact evidence vocabularies,
  clock-kind compatibility, Nyquist bounds, canonical digests; the
  reference plan mirrors canonical practice (diamagnetic loop, drive reference, end-loss array, flute probe array, synthetic oscillator);
  `computational_prototype` (ADR 0003,
  `VALIDATION.md#diagnostic-and-clock-semantics`). No ingress is
  declared; the SPO semantic-profile state remains `not_declared`.

- **Level-0 device physics** (landed 2026-09-02) — published mirror
  scalings and closed forms of the WHAM physics basis and the tandem
  confinement study evaluated on the validated configuration: diamagnetic
  mirror ratio and potential-modified loss boundary, collisional time
  scales, classical and gas-dynamic confinement scalings with the regime
  disposition, FLR interchange criterion, fast-ion adiabaticity, and the
  tandem Pastukhov chain with the ambipolar-hole energy; a canonical
  `Level0PhysicsRecord`, the shared numerics kernels pinned by commit and
  inventory digest, optional native kernels bit-exact with the Python
  floor, and a standard-conformant benchmark; `computational_prototype`
  (ADR 0005, ADR 0006, `VALIDATION.md#level-0-device-physics`).
  Follow-ups under the same capability: fusion power with the reactivity
  kernel once the library carries it, the `m = 1` vortex conditions once
  a curvature scale exists at level 2, and the plug electron potential
  solved at level 1.

- **Device 3D model** (landed 2026-09-03) — the mechanical envelope of
  the assembly (vessel, two coil pairs, expansion tanks, end walls) and
  the ten analytic bodies derived from it, on the shared geometry kernels.
  The plasma body is a **flux tube**, not a cylinder: its radius follows
  the declared axial field by flux conservation, and the build refuses a
  design whose column does not pass the mirror-coil bore. Canonical
  record, aperture clearances, open-format exports, bit-exact native
  parity and a standard-conformant benchmark; `computational_prototype`
  (ADR 0007, `VALIDATION.md#device-3d-model`). Follow-ups under the same
  capability: a resolved central-cell coil set once a field model exists
  at level 1, and the biased limiter and end-ring hardware once they are
  more than declarations.
- **Device CAD model** (landed 2026-09-03) — the same ten bodies as exact
  B-rep solids on the pinned OpenCASCADE kernel through the shared CAD
  kernels, with per-body evidence against the analytic closed forms, a
  deterministic normalised STEP export and an optional `cad` extra so the
  back-end is never a condition of installing the package;
  `computational_prototype` (ADR 0008, `VALIDATION.md#device-cad-model`).

## Planned (no implementation exists; ordering is not a commitment)
1. **Safety-envelope declaration** — machine-readable operational envelope
   (coil, beam, potential, and end-tank bounds) consumed by the CONTROL
   adapter contract.
2. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
3. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for open-field-line transport and
   velocity-space surfaces, strictly after the family migration gate
   proves exact replacement; no solver code is copied.
4. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Magnetic-cusp devices, electrostatic devices, the levitated dipole,
toroidal systems, pinches, inertial and magneto-inertial systems, generic
controller mathematics, machine-protection logic, and any direct actuation
path.
