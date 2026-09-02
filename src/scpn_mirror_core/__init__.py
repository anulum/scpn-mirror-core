# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device capability package

"""Device capability models of the SCPN magnetic-mirror device family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics`` and ``level0_device_physics`` capabilities
at ``computational_prototype`` maturity: validated parameter objects,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, documented consistency estimates, published
mirror scalings and closed forms evaluated on the validated configuration
through the pinned shared numerics kernels, canonical serialisation with
SHA-256 digests, and data-only pins to the SPO registries. No claim about
any real machine or diagnostic is made anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_mirror_core.configuration import (
    GAS_DYNAMIC_MIN_MIRROR_RATIO,
    LOSS_CONE_FRACTION_ADVISORY,
    OWNED_CONFIGURATIONS,
    TANDEM_PLUG_COUNT,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_mirror_core.errors import (
    DeviceConfigurationError,
    DiagnosticPlanError,
    NumericsError,
)
from scpn_mirror_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    CandidateProfile,
    ClockKind,
    ClockModel,
    ClockRelation,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    ObservabilityBinding,
    ObservabilityClass,
    ReferenceFrame,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)
from scpn_mirror_core.parameters import CellLayout, MirrorField
from scpn_mirror_core.physics import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Adiabaticity,
    CollisionTimes,
    ConfinementScalings,
    FlrCriterion,
    Level0PhysicsRecord,
    LossBoundary,
    MirrorRatio,
    ModelInputs,
    TandemConfinement,
    TandemInputs,
    adiabaticity,
    collision_times,
    confinement_scalings,
    flr_criterion,
    level0_physics,
    loss_boundary,
    mirror_ratio,
    tandem_confinement,
)
from scpn_mirror_core.plan_envelope import (
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

__version__: Final = "0.1.0.dev0"

__all__ = [
    "APPLICABLE_CANDIDATES",
    "CATALOGUE_BINDING",
    "GAS_DYNAMIC_MIN_MIRROR_RATIO",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "LOSS_CONE_FRACTION_ADVISORY",
    "OWNED_CONFIGURATIONS",
    "TANDEM_PLUG_COUNT",
    "Adiabaticity",
    "CandidateProfile",
    "CellLayout",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "CollisionTimes",
    "ConfinementScalings",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "DiagnosticPlanError",
    "FlrCriterion",
    "FrameKind",
    "Level0PhysicsRecord",
    "LossBoundary",
    "MirrorField",
    "MirrorRatio",
    "ModelInputs",
    "NumericsError",
    "ObservabilityBinding",
    "ObservabilityClass",
    "PlanEnvelope",
    "ReferenceFrame",
    "RegistryBinding",
    "SemanticCarrier",
    "TandemConfinement",
    "TandemInputs",
    "__version__",
    "adiabaticity",
    "collision_times",
    "configuration_from_bytes",
    "configuration_from_record",
    "confinement_scalings",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "flr_criterion",
    "level0_physics",
    "loss_boundary",
    "mirror_ratio",
    "plan_from_bytes",
    "plan_from_record",
    "tandem_confinement",
    "verify_envelope",
]
