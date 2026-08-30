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

## Planned (no implementation exists; ordering is not a commitment)

1. **Device configuration model** — typed configuration policy for the
   mirror family (cell layouts, mirror-ratio envelopes, plugging schemes,
   heating and beam inventory), with evidence-maturity target
   `computational_prototype`.
2. **Diagnostic and clock semantics** — declared axial-profile channels,
   end-loss analysers, velocity-space indicators, and clock identities
   aligned with the SCPN Phase Orchestrator semantic profile.
3. **Safety-envelope declaration** — machine-readable operational envelope
   (coil, beam, potential, and end-tank bounds) consumed by the CONTROL
   adapter contract.
4. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
5. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for open-field-line transport and
   velocity-space surfaces, strictly after the family migration gate
   proves exact replacement; no solver code is copied.
6. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Magnetic-cusp devices, electrostatic devices, the levitated dipole,
toroidal systems, pinches, inertial and magneto-inertial systems, generic
controller mathematics, machine-protection logic, and any direct actuation
path.
