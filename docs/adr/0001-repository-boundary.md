<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)  
**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. The registry's `magnetic_open` family
spans several distinct confinement principles (mirrors, cusp, dipole); a
boundary decision was needed on which of them share one repository.

## Decision

1. `SCPN-MIRROR-CORE` owns exactly three registry configurations:
   `simple_magnetic_mirror`, `tandem_mirror`, and `gas_dynamic_mirror`.
   All three are linear open-field devices whose defining physics is the
   axial mirror-force loss channel; cell count, plugging scheme, and
   collisionality regime are configuration parameters within one family.
2. The repository owns device-level truth only: linear-mirror
   configuration policy, axial-loss and end-plug semantics, quasi-steady
   lifecycle definitions, axial-profile diagnostic and clock declarations,
   actuator-response model boundaries, the safety-envelope declaration,
   and the device-owned CONTROL adapter specification.
3. Solver mathematics remains in `SCPN-FUSION-CORE` until an exact surface
   passes the family migration gate. No solver code is copied here.
4. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only).
   Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation remains in `SCPN-STUDIO`; this project is
   `not_federated`.
5. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **One repository for the whole `magnetic_open` registry family**
  (mirrors + cusp + dipole): rejected — the cusp confines at a sheath-like
  high-beta boundary between point and line cusps, and the levitated
  dipole confines in the closed-line field of an internal floating coil;
  neither shares the linear axial-loss physics, driver set, or lifecycle
  of mirror machines (surfaces 1, 2, and 3 differ).
- **Separate repositories per mirror variant**: rejected — the three
  variants share all five boundary surfaces; the split would triplicate
  contracts for parameter differences (cell count, collisionality).
- **Absorbing solver code at scaffold time**: rejected — violates the
  migration gate.

## Consequences

- Downstream consumers get one stable identity per mirror configuration
  and a manifest to bind against.
- The validator fails on any capability or claim entry while maturity is
  `architecture_only`.
- Boundary changes require a portfolio-level map change first; a future
  ADR records any such change here.
