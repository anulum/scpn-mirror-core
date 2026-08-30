<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — Architecture summary
-->

# Architecture summary

`SCPN-MIRROR-CORE` is the device-family owner for magnetic-mirror systems
(simple, tandem, and gas-dynamic mirrors) inside the SCPN Reactor Systems
Research Group. The repository is currently `architecture_only`: it defines
the device boundary, its ecosystem contracts, and the validation tooling
that enforces both, and it implements no reactor capability.

The authoritative architecture record is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The ownership decision and
its consequences are fixed in
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).

Boundary in one paragraph: this repository owns magnetic-mirror plant and
experiment truth — configuration policy for linear open-field devices
confined axially by mirror forces (loss-cone kinetics, end-cell
electrostatic plugging, gas-dynamic outflow regimes), quasi-steady
lifecycle semantics with instability-burst and plug-collapse records,
axial-profile diagnostic and clock declarations, actuator-response
boundaries, safety-envelope declarations, and the device-owned CONTROL
adapter specification. Solver mathematics stays in `SCPN-FUSION-CORE`;
typed semantics stay in `SCPN-PHASE-ORCHESTRATOR` (review-only); admitted
control actions are formed only by `SCPN-CONTROL`; independent machine
protection keeps the final veto; portfolio presentation belongs to
`SCPN-STUDIO`, towards which this project is `not_federated`.
