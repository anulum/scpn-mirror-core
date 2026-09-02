# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — level-0 device physics

"""Level-0 device physics of the magnetic-mirror family.

Published scalings and closed forms of the WHAM physics basis (Endrizzi et
al. 2023) and the tandem confinement study (Frank et al. 2025) evaluated
on the validated device configuration: the diamagnetic mirror ratio and
potential-modified loss boundary, the collisional time scales, the
classical and gas-dynamic confinement scalings, the FLR interchange
criterion, the fast-ion adiabaticity parameter and, for a tandem mirror,
the Pastukhov confinement chain. Every function is a closed-form
evaluation on the shared numerics kernels; no equation is solved and no
value describes a real machine. Design records: ADR 0005, ADR 0006.
"""

from __future__ import annotations

from scpn_mirror_core.physics.adiabaticity import (
    ADIABATICITY_THRESHOLD,
    Adiabaticity,
    adiabaticity,
    require_fraction,
)
from scpn_mirror_core.physics.collisions import (
    CollisionTimes,
    collision_times,
    ion_scattering_time,
    three_halves,
)
from scpn_mirror_core.physics.confinement import (
    REGIME_CLASSICAL,
    REGIME_GAS_DYNAMIC,
    ConfinementScalings,
    classical_confinement_time,
    confinement_scalings,
    gas_dynamic_confinement_time,
)
from scpn_mirror_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    TandemInputs,
    level0_physics,
)
from scpn_mirror_core.physics.mirror import (
    LossBoundary,
    MirrorRatio,
    loss_boundary,
    mirror_ratio,
    require_midplane_beta,
)
from scpn_mirror_core.physics.numerics import (
    ATOMIC_MASS_KG,
    ELEMENTARY_CHARGE_C,
    KEV_J,
    exponential,
    natural_log,
    power,
)
from scpn_mirror_core.physics.stability import (
    FLR_MODE_THRESHOLD,
    FlrCriterion,
    critical_mode_number,
    flr_criterion,
    ion_gyromotion,
)
from scpn_mirror_core.physics.tandem import (
    TandemConfinement,
    pastukhov_function,
    tandem_confinement,
)

__all__ = [
    "ADIABATICITY_THRESHOLD",
    "ATOMIC_MASS_KG",
    "ELEMENTARY_CHARGE_C",
    "FLR_MODE_THRESHOLD",
    "KEV_J",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "REGIME_CLASSICAL",
    "REGIME_GAS_DYNAMIC",
    "Adiabaticity",
    "CollisionTimes",
    "ConfinementScalings",
    "FlrCriterion",
    "Level0PhysicsRecord",
    "LossBoundary",
    "MirrorRatio",
    "ModelInputs",
    "TandemConfinement",
    "TandemInputs",
    "adiabaticity",
    "classical_confinement_time",
    "collision_times",
    "confinement_scalings",
    "critical_mode_number",
    "exponential",
    "flr_criterion",
    "gas_dynamic_confinement_time",
    "ion_gyromotion",
    "ion_scattering_time",
    "level0_physics",
    "loss_boundary",
    "mirror_ratio",
    "natural_log",
    "pastukhov_function",
    "power",
    "require_fraction",
    "require_midplane_beta",
    "tandem_confinement",
    "three_halves",
]
