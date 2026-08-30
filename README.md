<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — README
-->

# SCPN Mirror Core

Governed device-family repository for magnetic-mirror fusion systems within
the SCPN Reactor Systems Research Group. This repository is the designated
owner of device-level truth for the three mirror configurations of the SCPN
Phase Orchestrator reactor registry: `simple_magnetic_mirror` (linear
magnetic mirror), `tandem_mirror` (multi-cell linear mirror), and
`gas_dynamic_mirror` (collisional linear mirror).

**Evidence maturity: `architecture_only`.** The repository currently defines
boundaries, contracts, and validation infrastructure. It implements no
reactor capability and makes no scientific claim. The capability and claim
inventories are empty by design and verified empty by the domain validator.

## Scope

This repository owns, for the magnetic-mirror device family:

- the device boundary: plant and experiment truth, lifecycle, and
  configuration policy for open-field-line linear devices confined axially
  by magnetic mirror forces — the single-cell mirror (loss-cone-governed
  kinetic confinement), the tandem mirror (end-cell electrostatic plugging
  of a central cell), and the gas-dynamic mirror (high-collisionality
  regime with mirror ratio-governed outflow);
- axial-confinement semantics: loss-cone population declarations,
  end-plug and thermal-barrier potential declarations, and expander/end-tank
  boundary conditions;
- diagnostic semantics, reference frames, and clock identity declarations;
- actuator-response model boundaries and the declared safety envelope;
- the device-owned CONTROL adapter specification;
- the binding to the SCPN Phase Orchestrator reactor registry
  (version `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`);
- the machine-readable domain manifest `reactor-domain.json` and the derived
  Studio portfolio descriptor (integration state `not_federated`).

## Explicit exclusions

- **Magnetic cusp confinement**: `SCPN-MAGNETIC-CUSP-CORE`.
- **Electrostatic confinement** (gridded IEC and Polywell-style devices):
  `SCPN-IEC-CORE`.
- **Levitated dipole**: `SCPN-LEVITATED-DIPOLE-CORE`.
- **Toroidal systems**: `SCPN-TOKAMAK-CORE` and the other closed-field
  device cores.
- **Solver mathematics and validation evidence**: `SCPN-FUSION-CORE` until
  an exact surface passes the reactor family migration gate; no solver code
  exists in, or was copied into, this repository.
- **Typed signal semantics and comparability**: `SCPN-PHASE-ORCHESTRATOR`
  (review-only output; never actuation).
- **Control admission and action formation**: `SCPN-CONTROL` is the sole
  software authority that forms an admitted `ControlAction`.
- **Machine protection**: independent systems retain the final veto.
- **Portfolio presentation, identity, entitlement, and execution gating**:
  `SCPN-STUDIO`.

## Non-claims

This repository is not machine-ready, not safety-certified, and not
reactor-ready. It contains no implemented solver, no controller, no
benchmark result, no experimental correlation, no dataset, and no
deployable artefact. Cell-count, plugging-scheme, and fuel-cycle choices
are configuration facets, not separate claims. None of the
evidence-maturity states defined by the reactor family standard has been
reached beyond `architecture_only`.

## Architecture

The five-surface boundary and the position of this repository in the SCPN
ecosystem are defined in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and
fixed by
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).
The threat model is in [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md); the
CONTROL adapter contract is in
[`docs/CONTROL_ADAPTER_SPECIFICATION.md`](docs/CONTROL_ADAPTER_SPECIFICATION.md).

## Validation

Every gate currently active in this repository is listed in
[`VALIDATION.md`](VALIDATION.md). The local sequence is:

```bash
make lint        # ruff check + ruff format --check
make typecheck   # mypy --strict tools tests
make test        # pytest with 100 % statement and branch coverage on tools/
make validate    # domain manifest, descriptor, and inventory checks
make preflight   # the full fail-closed gate sequence
```

## Security

See [`SECURITY.md`](SECURITY.md) for the supported states and the private
reporting route (protoscience@anulum.li).

## Licensing

AGPL-3.0-or-later for the public repository, with a commercial licence
available (see [`NOTICE.md`](NOTICE.md)). Licence texts are under
[`LICENSES/`](LICENSES/); machine-readable licensing metadata follows
REUSE 3.x (`REUSE.toml`).

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff). No release,
version, or DOI exists yet; cite the repository state you inspected.
