<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Mirror Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-MIRROR-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`MirrorField`, `CellLayout`,
  `DeviceConfiguration`) rejecting non-finite values, a mirror ratio at
  or below one, and the hard class invariants: exactly two end plugs
  for `tandem_mirror`, zero for the other classes (Post, Nucl. Fusion
  27 (1987) 1579), and the collisional-regime declaration exactly for
  `gas_dynamic_mirror` (Mirnov & Ryutov, 1979) — every rejection branch
  is tested.
- Advisory consistency findings with documented bounds, reported and
  never clamped: an isotropic loss-cone fraction
  `f_lc = 1 - sqrt(1 - 1/R_m)` above one half, and a gas-dynamic mirror
  ratio below ten.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are advisory regime checks, not confinement, transport,
  or stability results; no benchmark, dataset, solver, controller, or
  experimental correlation exists in this repository.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design records:
`docs/adr/0005-level0-device-physics.md` and
`docs/adr/0006-shared-numerics-kernels.md`). Sources (both CC BY 4.0):
D. Endrizzi et al., "Physics basis for the Wisconsin HTS Axisymmetric
Mirror (WHAM)", J. Plasma Phys. 89 (2023) 975890501; S. Frank et al.,
"Confinement performance predictions for a high field axisymmetric tandem
mirror", J. Plasma Phys. 91 (2025) E110.

What is exercised, all under the 100 % statement-and-branch coverage gate
(`src/scpn_mirror_core/physics/`):

- **Numerics substrate** (`numerics.py`): the natural logarithm, the
  exponential and the real power are the pinned shared kernel library's
  (`scpn-reactor-kernels`, kernel `numerics_transcendental`; commit and
  inventory digest in `reactor-domain.json`, `kernel_library`); tests
  prove each wrapper returns the library value bit for bit and re-raises
  the library's domain refusal as `NumericsError` (a configuration error).
  The manifest block is validated field by field and a contract test
  proves the manifest, the `pyproject.toml` dependency, the installed
  library version, `rust/Cargo.toml`, `rust/Cargo.lock` and the CI install
  steps name one commit.
- **Mirror ratio and loss boundary** (`mirror.py`; Endrizzi eq. 3.6,
  Frank eqs. 2.3–2.5): `R_m = R_vac / sqrt(1 - beta)` with beta refused
  outside `[0, 1)`; the loss boundary `sin^2 theta = (1 + q Delta phi / E)
  / R_m` for ions and electrons, with the electrons fully confined below
  `e Delta phi` (the source: "only electrons with energies above 5 T_e
  leave") and a cone at or beyond unity reported as "no trapped region";
  at zero potential the isotropic fraction equals the configuration's
  `loss_cone_fraction()` bit for bit. The typography of the printed
  eq. 2.5b is resolved by the source's own statement (ADR 0005 item 3).
- **Collisional time scales** (`collisions.py`; eqs. 3.1–3.3): the
  engineering forms at unit inputs (5 ms, 1/8 ms, 5.8 μs), the stated
  scalings, and the source's identity `tau_s = tau_ii` at
  `T_e = E_i / 40^(2/3)` (reproduced to `1e-14` relative; the source says
  "about `E_i / 10`", and the value lies between `E_i / 12` and `E_i / 10`).
- **Confinement scalings** (`confinement.py`; eqs. 3.4–3.5): the classical
  scaling equals 250 ms at the reference point (n20 = 1, 100 keV,
  `R_m = 10`); the source's statement that beta from 0 to 0.9 gains "only
  50 %" is reproduced exactly (factor 1.5 at `R_vac = 10`); the gas-dynamic
  dimensional form `R_m L_p / c_s` with `c_s = sqrt(T_e / m_i)` reproduces
  the printed coefficient 5.2 within 3 % at 2.5 proton masses (5.09); the
  regime disposition follows the configuration's declaration.
- **FLR criterion** (`stability.py`; eq. 3.7): the source's worked case
  `a / rho_i = 4`, `L_p / a = 10` gives `m_crit = 0.8` ("all m >= 2 FLR
  stabilised"); the disposition switches at 2; the gyromotion definitions
  are tested as declared. The `m = 1` mode is not assessed.
- **Adiabaticity** (`adiabaticity.py`; §3.6): `alpha = L_B / rho_par`,
  its `B` and `1/f` scalings, the threshold 10, and the not-applicable
  report at zero parallel fraction. No printed numerical anchor exists
  (the source's `alpha ~ 10` case does not print `L_B`).
- **Tandem confinement** (`tandem.py`; Frank eqs. 3.2–3.7, 4.3):
  `phi_i = T_e ln(n_p / n_c)` refusing `n_p <= n_c`; `G(1) = sqrt 2
  ln(3 + 2 sqrt 2)` and monotony of `G`; `tau_ii` at `T_ic`; the
  combination identity of eq. 3.2 and `tau_c` below both channels; the
  ambipolar-hole energy absent when `R_m sin^2 theta <= 1`; an exponential
  outside the library's window refused as `NumericsError`. No printed
  numerical anchor exists for eq. 3.3; the record's digest is pinned as
  an immutability fixture.
- A composed `Level0PhysicsRecord` (`scpn.mirror-level0-physics.v1`
  `1.0.0`) with canonical bytes, SHA-256 digest, fixed non-claims and two
  pinned reference digests (simple and tandem), built from the validated
  configuration and explicit `ModelInputs` / `TandemInputs` (required
  exactly for a tandem); every input rejects non-positive and non-finite
  values.
- **Native parity**: the Rust crate in `rust/` mirrors every kernel with
  identical operation order on the library's Rust crate at the pinned
  commit; `tests/test_physics_native_parity.py` compares float64 bit
  patterns over a 72-point grid of models 1–3 plus the FLR, adiabaticity
  (including the not-applicable branch) and tandem (including the absent
  hole energy) inputs, and the refusal paths of the bindings.
- **Benchmark**: `benchmarks/level0_physics.py` per the ecosystem
  benchmark standard; results in `docs/benchmarks.md` and the committed
  local artefact `benchmarks/results/level0_physics.local.json`.

Bounded claims — what is NOT claimed:

- Every number is a closed-form evaluation of published scalings and closed
  forms on a synthetic configuration; no Fokker–Planck, ambipolar,
  equilibrium or stability equation is solved, and no eigenvalue problem
  exists here.
- The anchors reproduce numbers and statements printed in the sources;
  they are not correlations with experimental data; the printed
  coefficient of the gas-dynamic time is matched only to the stated 3 %.
- No fusion power, gain, breakeven, reactivity or `m = 1` stability
  statement is made; the plug electron potential and the field-gradient
  scale length are declared inputs, not results.
- No value describes, approximates or validates any real machine; the
  benchmark measures per-point evaluation cost of two implementations of
  the same closed forms, not physics.
- Maturity stays `computational_prototype`.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- The nullable `timing_uncertainty_s` member, declared `null` on every
  channel because no event-relative candidate is applicable here; a
  non-null value is refused. This keeps the channel shape identical across
  the portfolio under envelope 1.1.0.
- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, and incomplete candidate coverage —
  every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- A reference plan mirroring canonical practice with synthetic
  declarations: diamagnetic loop, drive reference, end-loss array, flute probe array, synthetic oscillator, each bound to its clock domain.
- Documented advisory band checks with their sources stated in the
  code: mirror interchange/flute activity in the 0.1–100 kHz scale and ICRF-to-ECRH drive frequencies (Post 1987); findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for this device family remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_mirror_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). The envelope is `1.1.0`, adding
`manifest_sha256` — the SHA-256 of the committed canonical
`reactor-domain.json` — verified in tests against the committed file.
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion;
`1.1.0` remains historical custody at the consumer) adds three typed
declaration surfaces, every branch under the 100 % statement-and-branch
gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; no `timing_marker` (no
  event-relative candidate is applicable); numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`) between declared
  frames: kind admissibility fixed by frame-kind pair (`flux_mapping`
  for machine↔flux, flux↔Boozer, field-line↔machine; `projection` for
  blanket↔machine; `rigid` for chamber↔beamline), `equilibrium_dependent`
  exactly for flux mappings, at most one transformation per frame pair,
  sorted by source then target, and — with two or more frames — a
  connected transformation graph. Methods are declarations;
  `evidence_claimed` is always `False`.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.
