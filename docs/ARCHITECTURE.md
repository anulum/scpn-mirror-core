<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-MIRROR-CORE` is the device-family owner for magnetic-mirror systems
in the SCPN Reactor Systems Research Group portfolio. The repository is
`architecture_only`: every section below describes boundaries and
contracts, not implemented capability. The capability and claim inventories
are empty; both derived artefacts are generated and drift-checked.

## The five-surface boundary

1. **Governing confinement physics** — open-field-line axial confinement by
   magnetic mirror forces in linear geometry. The three owned
   configurations span the family's physics space: the
   `simple_magnetic_mirror` (kinetic, loss-cone-governed confinement with
   velocity-space instability boundaries), the `tandem_mirror` (a central
   cell axially plugged by end-cell electrostatic potentials, including
   thermal-barrier operation), and the `gas_dynamic_mirror`
   (high-collisionality regime where outflow follows gas-dynamic scaling
   with the mirror ratio). They share the linear open geometry, the axial
   loss channel as the defining confinement question, expander/end-tank
   boundary physics, and one driver and lifecycle class. Cusp geometries
   (point/line-cusp boundary confinement), electrostatic devices, the
   levitated dipole, and all toroidal systems fail this sharing test and
   are excluded.
2. **Primary driver and energy delivery** — steady or long-pulse
   solenoidal and mirror-coil systems establishing the axial field
   profile, with neutral-beam injection (including sloshing-ion
   populations), electron- and ion-cyclotron heating, and end-cell
   potential-control systems as the principal drivers.
3. **Plant and shot lifecycle** — quasi-steady lifecycle: field
   energisation, plasma build-up (gas or plasma-gun start, beam capture),
   sustained operation with axial-loss balance, and controlled
   termination. Device-level hazard semantics cover velocity-space
   (loss-cone-driven) instability bursts and end-plug potential collapse.
4. **Diagnostic, reference-frame, and clock model** — axial-profile
   conventions (field, density, and potential along the machine axis),
   end-loss analyser and expander diagnostics, velocity-space population
   declarations, laboratory-frame geometry, and clock identities for
   quasi-steady operation.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE`, review-only semantics towards
   `SCPN-PHASE-ORCHESTRATOR`, and the device-owned CONTROL adapter
   specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-MIRROR-CORE (device truth: linear open-field policy, axial-loss
                  semantics, end-plug declarations, safety envelope,
                  adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   └──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated, truthfully empty inventory |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `tools/` |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`; unknown
  schemas are rejected by consumers.
- The Studio descriptor is derived deterministically and embeds the
  manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at `0.1.0-spec`.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`.

## What would change this architecture

Acceptance of a FUSION solver seam through the family migration gate,
ratification of an SPO `ControlIntent`-class contract, or Studio federation
after a real capability passes producer and consumer gates — each recorded
as a versioned contract change in a new ADR.
