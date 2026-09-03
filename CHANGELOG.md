<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — CHANGELOG
-->

# Changelog

## [Unreleased]

### Added

- Device 3D model (`src/scpn_mirror_core/geometry/`), the fourth
  implemented capability at `computational_prototype` (ADR 0007): a
  validated `DeviceGeometry` of thirteen SI envelope parameters
  (central-cell vessel, central-cell coil pair, mirror-coil pair,
  expansion tanks, end walls) and ten named, closed, outward-oriented
  bodies derived from it. Nine are surfaces of constant radius; the tenth
  is not. The confined plasma of a mirror is a **flux tube**, so it is
  built as a surface of revolution through the `(z, radius)` profile that
  a **declared** axial field profile implies under flux conservation,
  `r(z) = r_mid sqrt(B_mid / B(z))` — the one physical relation this tier
  applies. The mirror coils are centred on the throats at
  `±central_cell_length_m / 2`, read from the validated configuration, so
  the cell length has one home. The build cross-checks the declared
  profile against the configuration's own `b_min_t` and `b_max_t`,
  refuses a field maximum away from a throat, and **refuses a design in
  which the column does not pass the bore it has to clear**, naming the
  section; the record carries the per-section aperture clearance. Open
  format exports (binary STL, glTF 2.0 binary) carry the declared field
  profile as document provenance. The geometry, profile and CAD kernels
  are the pinned shared library's, re-pinned to the commit that carries
  them; bit-exact native parity against the library's native module
  covers all ten bodies, the profiled tube included, plus its exact
  frustum-stack closed forms. Consumer contract in
  `docs/DEVICE_3D_MODEL_CONTRACT.md`, benchmark
  `benchmarks/device_model_3d.py` with a committed local artefact.
- Device CAD model (`src/scpn_mirror_core/geometry/cad.py`), the fifth
  implemented capability at `computational_prototype` (ADR 0008): the
  same ten bodies as exact B-rep solids on the pinned third-party
  OpenCASCADE kernel through the shared library's CAD kernels, with the
  flux tube revolved through the same profile the tessellation is built
  from. Every body is checked fail-closed against its analytic closed
  form within `1e-9` relative — for the flux tube that form is the exact
  frustum-stack sum of its linear profile — against the declared faceting
  chord-deficit bound and against the tier-G1 mesh within the exact
  polygon-deficit bound. Normalised deterministic STEP export with its
  digest in the record. **The CAD back-end is an optional extra**
  (`pip install ".[cad]"`) naming the same library commit as the base
  dependency, proven by a contract test: the other four capabilities work
  without a B-rep kernel, and only two CI jobs install it. Benchmark
  `benchmarks/device_model_cad.py` with a committed local artefact.

- Level-0 device physics (`src/scpn_mirror_core/physics/`), the third
  implemented capability at `computational_prototype` (ADR 0005): the
  diamagnetic mirror ratio and the potential-modified loss boundary, the
  collisional time scales, the classical and gas-dynamic confinement
  scalings with the regime disposition, the FLR interchange criterion,
  the fast-ion adiabaticity parameter and, for a tandem mirror, the
  Pastukhov confinement chain with the ambipolar-hole energy — with a
  canonical `Level0PhysicsRecord`, explicit `ModelInputs` and
  `TandemInputs`, and two pinned reference digests. The transcendental
  functions are the shared kernel library's (`scpn-reactor-kernels`,
  ADR 0006): the library is the one runtime dependency pinned to a commit
  object in `pyproject.toml`, the manifest records the same commit, the
  library's kernel-inventory digest and the consumed kernel in a new
  optional `kernel_library` block enforced by the validator, and declares
  the excluded domain `shared_physics_geometry_and_numerics_kernels`.
  Native kernels (`rust/`, crate `scpn-mirror-rs` depending on the
  library's Rust crate at the same commit, optional distribution
  `scpn-mirror-native`) reproduce every value bit for bit, proven by
  parity tests; a standard-conformant benchmark
  (`benchmarks/level0_physics.py`) with a committed local artefact and
  `docs/benchmarks.md`. The manifest declares the capability and the
  owned domain `analytic_device_physics_models`; descriptor and inventory
  regenerated; the envelope fixture regenerated for the new
  `manifest_sha256` (plan bytes unchanged). Gates extended: `mypy` scope
  includes `benchmarks/` (and `make typecheck` now covers `src/`), CI
  installs the package with its pinned dependency, a `rust` CI job runs
  the crate gates, parity and a benchmark smoke, `make rust` locally.

- Diagnostic-plan depth: per-channel signal inventories, frame
  transformations with a fixed kind-admissibility table and connectivity
  rule, and a clock topology partitioning the physical clocks into rooted
  domains with a star of relations to the reference root. Envelope
  `scpn.reactor-diagnostic-plan-envelope.v1` bumped to `1.2.0`; the
  fixture is regenerated from the public surface and re-pinned. All new
  members are declarations: no observation, phase, mapping, or control
  authority is created.

### Fixed

- Added the nullable `timing_uncertainty_s` channel member (always `null`;
  no event-relative candidate is applicable) so the diagnostic-plan
  channel shape matches the portfolio-uniform envelope 1.1.0 contract;
  fixture regenerated and re-pinned.

### Added

- Local gate parity with the wider ecosystem: the pre-commit chain now
  also runs REUSE licensing compliance and a typographical checker
  (`_typos.toml` carries the deliberate reactor vocabulary), and adds
  the upstream YAML, TOML, large-file and private-key guards. Licensing
  and spelling were previously verified only in hosted CI, so a broken
  REUSE annotation — including the aggregate annotation that covers the
  binary header images — could reach a push before being caught.
- Generated repository header artwork: `docs/assets/generate_header.py`
  renders three deterministic 1280x640 images from the repository's own
  domain surface (the magnetic bottle used by the README, the three
  owned cell layouts with the plug invariant, and the loss cone).
- Modular hosted-workflow surface per the ecosystem workflow-modularity
  standard: `ci.yml` reduced to a coordinator with a stable fail-closed
  `gate` job, single-responsibility reusable workflows for static
  analysis/repository policy and for tests, a versioned machine-readable
  inventory (`.github/workflow-inventory.json`,
  `scpn.workflow-inventory.v1` `1.0.0`), and a fail-closed modularity
  guard (`tools/audit_workflows.py`) enforced locally (preflight gate,
  pre-commit hook) and in hosted CI. The duplicate documentation-links
  step was removed from the CI chain; `docs.yml` remains the single
  owner of documentation validation.

- Typed reference frames, clock synchronisation relations (synthetic
  bounds only; no correlation evidence claimed), and per-channel
  acquisition windows and element counts in the diagnostic model;
  hardened decoders (recursive exact-key, duplicate-member, and
  byte-canonical refusal in both codecs); envelope `1.1.0` adding
  `manifest_sha256` over the committed canonical `reactor-domain.json`
  (fixture regenerated; byte hash re-pinned in tests).

- Portable diagnostic-plan envelope
  (`src/scpn_mirror_core/plan_envelope.py`,
  `scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): a
  producer-owned, canonically serialised wrapper carrying project
  identity, exact owned configurations, capability and maturity,
  synthetic/review-only/non-actuating statements, both SPO registry
  pins, the inner plan's SHA-256, the producer revision, and fixed
  no-observation/no-control non-claims; strict parsers refuse unknown,
  duplicate, and non-finite members, and an immutable committed fixture
  exercises the exchange end to end.

- Diagnostic and clock semantics model
  (`src/scpn_mirror_core/observability.py`), the second implemented
  capability at `computational_prototype`: frozen clock, channel,
  deferral, and plan objects aligned fail-closed with the pinned SPO
  observability-profile catalogue (candidate applicability, carrier
  admissibility, exact class-fixed evidence vocabularies, clock-kind
  compatibility, Nyquist bounds); cited advisory band checks; canonical
  serialisation with SHA-256 digests and strict NaN-rejecting round-trip
  parsing (design record `docs/adr/0003-diagnostic-clock-semantics.md`).

- Device configuration model (`src/scpn_mirror_core/`), the first implemented
  capability at `computational_prototype`: validated frozen parameter
  objects with device-specific invariants and documented, cited
  consistency estimates; canonical serialisation with SHA-256 digests
  and strict NaN-rejecting round-trip parsing; a data-only pin to the
  SPO reactor registry; and the reactor-domain validator branch
  enforcing populated capability inventories with the ADR 0002
  evidence-maturity ceiling rule (design record
  `docs/adr/0002-device-configuration-model.md`).

- Architecture-only repository scaffold: governance, security, licensing,
  REUSE metadata, contribution and support policies, and citation metadata.
- Machine-readable domain manifest `reactor-domain.json` binding the project
  to SCPN Phase Orchestrator reactor registry `1.0.0`
  (configurations `gas_dynamic_mirror`, `simple_magnetic_mirror`,
  `tandem_mirror`).
- Device-owned CONTROL adapter specification and threat model.
- Derived Studio portfolio descriptor (`not_federated`) and generated
  capability inventory (zero implemented capabilities).
- Validation tooling: domain-manifest validator, descriptor derivation and
  inventory generation with drift checks, and a fail-closed preflight
  orchestrator, each with statement- and branch-complete tests.
- Continuous-integration, code-scanning, security-audit, documentation,
  SBOM, pre-commit, and Scorecard workflow definitions (read-only
  permissions; no publication or deployment workflows).

### Changed

- Native surface documentation is now a compiler gate, not a habit: the crate
  denies `missing_docs`, `missing_debug_implementations` and `unsafe_code`, and
  denies rustdoc's broken and private intra-doc links and invalid Rust code
  blocks. `cargo doc --no-deps` joins the local `rust` target and the hosted
  `rust` job, so a public item that ships without documentation fails the build
  rather than accumulating as debt for the next reader.

- Studio portfolio descriptor schema ratified at version 1.1.0 after
  downstream review, before any consumer adoption (1.0.0 superseded
  unconsumed): canonical JSON Schema published in-repository with a strict
  unknown-field policy, explicit source repository, nullable lifecycle
  evidence pointer, nullable versioned control-intent reference, ratified
  capability item shape, and a machine-protection object (independent
  final-veto owner with availability `not_assessed`) replacing the former
  boolean flag.
