<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: published mirror scalings and closed forms with native parity

Status: accepted (2026-09-02). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

Until this record the repository carried no physics beyond the loss-cone
fraction and the gas-dynamic advisory of the configuration model. Every
device manifest excludes `solver_mathematics_and_validation_evidence`
(owner SCPN-FUSION-CORE), and no FUSION seam covers the mirror family. The
device owner therefore needs its own bounded, exercised, published physics:
closed forms and scalings from the family's own literature, evaluated on
the validated configuration, without solving any equation. Two open-access
sources carry them in published form with printed statements that serve as
anchors: the WHAM physics basis (D. Endrizzi et al., J. Plasma Phys. 89
(2023) 975890501) and the tandem confinement study (S. Frank et al., J.
Plasma Phys. 91 (2025) E110), both CC BY 4.0.

## Decision

1. A new owned domain `analytic_device_physics_models` is declared in
   `reactor-domain.json`: device-owned closed-form and 0-D models from the
   device literature. It is disjoint from solver mathematics: no solver
   code is copied, no Fokker–Planck, ambipolar, equilibrium or stability
   equation is solved, and no FUSION seam is implied or consumed.
2. Six models, each with its published form cited in the module
   docstring, live one per module under `src/scpn_mirror_core/physics/`:
   the diamagnetic mirror ratio and the potential-modified loss boundary
   (Endrizzi eq. 3.6; Frank eqs. 2.3–2.5), the collisional time scales
   (Endrizzi eqs. 3.1–3.3), the classical and gas-dynamic confinement
   scalings with the regime disposition (Endrizzi eqs. 3.4–3.5), the FLR
   interchange criterion (Endrizzi eq. 3.7), the fast-ion adiabaticity
   parameter (Endrizzi §3.6) and, for `tandem_mirror` only, the Pastukhov
   confinement chain with the ambipolar-hole energy (Frank eqs. 3.2–3.7,
   4.3). A composed `Level0PhysicsRecord` serialises canonically with a
   SHA-256 digest and carries fixed non-claims.
3. One typographical ambiguity of a source is resolved by the source's own
   text and recorded in the evidence record: the printed loss boundary
   (Frank eq. 2.5b) shows the reciprocal fraction under the root, which at
   zero potential would exceed one; the form derived from the conservation
   of the magnetic moment and the energy reduces to the standard loss cone
   at zero potential, as the text states, and is the one implemented.
4. Declared modelling choices are stated, never hidden: the plasma
   half-length is half the central-cell length; the ion gyroradius uses
   ``v = sqrt(2 E_i / m_i)``; the gas-dynamic sound speed is
   ``sqrt(T_e / m_i)`` (the printed coefficient 5.2 is reproduced within
   3 % at 2.5 proton masses, which fixes the definition the source
   implies); the tandem ``tau_ii`` is Endrizzi eq. 3.2 at ``E_i = T_ic``;
   the plug electron potential is a declared input because Frank eq. 3.8
   is a transcendental equation; the field-gradient scale length is a
   declared input because a field model belongs to level 2.
5. Inputs the configuration does not carry are declared explicitly in
   `ModelInputs` and `TandemInputs` (required exactly for a tandem);
   nothing is defaulted silently. A zero parallel-velocity fraction and a
   non-positive ambipolar-hole denominator are reported as not applicable,
   never clamped.
6. The transcendental functions are the pinned shared kernel library's
   (ADR 0006); the Python floor uses only ``+ - * /``, ``sqrt`` and those
   kernels. Native kernels (`rust/`, crate `scpn-mirror-rs`, optional
   distribution `scpn-mirror-native` via maturin) mirror every evaluation
   with identical operation order on the library's Rust crate; parity
   tests compare float64 bit patterns, never tolerances. The pure-Python
   floor remains the public API and the default.
7. Performance numbers follow the ecosystem benchmark standard; the local
   artefact is committed and labelled non-isolated.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. VALIDATION states per model what is exercised and what is
not claimed; the anchors reproduce numbers and statements printed in the
sources, which is not a correlation with data. Fusion power (Frank eqs.
3.10–3.11) waits for the reactivity kernel and an arctangent kernel of the
library; the ``m = 1`` vortex conditions wait for a curvature scale at
level 2. The manifest change alters `manifest_sha256` inside the plan
envelope, so the envelope fixture is regenerated from the public surface
and re-pinned; the plan bytes and `plan_sha256` are unchanged.
