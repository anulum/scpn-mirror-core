<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ADR 0002: device configuration model
-->

# ADR 0002 — Device configuration model and evidence-maturity semantics

**Status:** accepted (2026-08-31)

**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The repository was established architecture-only (ADR 0001). The first
capability lane is the device configuration model for the three mirror
registry configurations this repository owns (`gas_dynamic_mirror`,
`simple_magnetic_mirror`, `tandem_mirror`). The claim boundary and
repository-level `evidence_maturity` semantics follow the family pilot.

## Decision

1. The package `scpn_mirror_core` implements the device configuration
   model as frozen, strictly typed value objects: the axial mirror
   field (``B_max``, ``B_min``), the cell layout (central-cell length
   and end-plug count), and the configuration container with a
   collisionality-class declaration.
2. Claim boundary — identical to the family pilot: internal-consistency
   validation, cited textbook estimates with documented bounds,
   canonical serialisation with SHA-256 digest, and the data-only SPO
   registry pin. No claim about any real machine; every exercised
   parameter set is a synthetic test fixture.
3. Hard class invariants: ``B_max > B_min > 0`` (a mirror ratio above
   one is the defining property of the family); `tandem_mirror`
   requires exactly two end-plug cells, `simple_magnetic_mirror` and
   `gas_dynamic_mirror` require zero (the tandem central cell "is
   flanked by two simple mirror end plugs": S. Frank et al., J. Plasma
   Phys. 91 (2025) E110, PDF p. 2); `gas_dynamic_mirror` requires the
   collisional-regime declaration and the other two classes forbid it —
   collisional confinement is the defining property of the gas-dynamic
   trap (V. V. Mirnov, D. D. Ryutov, Sov. Tech. Phys. Lett. 5 (1979)
   279, not on file; the filed WHAM physics basis, Endrizzi et al. 2023,
   PDF p. 2, sets the gas-dynamic regime apart by its strong sonic
   losses).
4. Advisory estimates, reported by `consistency_report()` and never
   clamped: the isotropic loss-cone fraction
   ``f_lc = 1 - sqrt(1 - 1/R_m)`` (derived from conservation of the
   magnetic moment: loss-cone edge at ``sin^2(theta) = 1/R_m``) above
   one half is
   flagged, and a `gas_dynamic_mirror` with ``R_m < 10`` is flagged
   (the gas-dynamic regime relies on a large mirror ratio).
5. Repository-level `evidence_maturity` = the highest state claimed by
   any capability entry; per-capability states are the authoritative
   claim surface.
6. Everything else is unchanged: review-only/non-actionable SPO
   profile, no adapter implementation, empty solver seams,
   `not_federated` Studio state, independent machine-protection veto,
   all non-claims.

## Consequences

- The Studio descriptor's `capabilities` array carries its first item
  (schema 1.1.0 data change only).
- The reactor-domain validator gains the populated-capabilities branch
  with the ceiling rule.
- Later lanes (axial-profile diagnostic semantics, safety envelope)
  build on these types; maturity advances per capability only with the
  evidence the family standard requires.

## Amendment 2026-10-31

The end-plug invariant and the loss-cone fraction were credited to
R. F. Post, Nucl. Fusion 27 (1987) 1579. That review is not on file and no
page of it was read for them. The end-plug count is now bound to the
filed Frank et al. (2025) text, and the loss-cone fraction is stated as
derived. No invariant, formula or threshold changed.
