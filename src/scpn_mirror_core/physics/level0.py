# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — level-0 physics record

"""Level-0 physics record of one validated mirror configuration.

The record composes the published closed forms and scalings of the WHAM
physics basis (D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501)
and, for a tandem mirror, of the tandem confinement study (S. Frank et
al., J. Plasma Phys. 91 (2025) E110) on the validated
:class:`~scpn_mirror_core.configuration.DeviceConfiguration` together with
the declared model inputs the configuration does not carry. The plasma
half-length of every model is half the central-cell length. It serialises
canonically with a SHA-256 digest and states its own non-claims: every
number is a closed-form evaluation on a synthetic configuration, at
``computational_prototype`` maturity; no equation is solved.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_mirror_core.configuration import DeviceConfiguration
from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import require_finite, require_positive
from scpn_mirror_core.physics.adiabaticity import (
    Adiabaticity,
    adiabaticity,
    require_fraction,
)
from scpn_mirror_core.physics.collisions import CollisionTimes, collision_times
from scpn_mirror_core.physics.confinement import (
    ConfinementScalings,
    confinement_scalings,
)
from scpn_mirror_core.physics.mirror import (
    LossBoundary,
    MirrorRatio,
    loss_boundary,
    mirror_ratio,
    require_midplane_beta,
)
from scpn_mirror_core.physics.stability import FlrCriterion, flr_criterion
from scpn_mirror_core.physics.tandem import TandemConfinement, tandem_confinement

LEVEL0_SCHEMA: Final = "scpn.mirror-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
LEVEL0_NON_CLAIMS: Final = (
    (
        "closed-form evaluation of published mirror scalings and closed forms on a "
        "synthetic configuration"
    ),
    (
        "no equation is solved: no Fokker-Planck, no self-consistent ambipolar "
        "potential, no equilibrium or stability eigenproblem"
    ),
    "no fusion power, gain, breakeven or m = 1 stability statement",
    (
        "no value describes or validates any real machine; the anchors reproduce "
        "numbers and statements printed in the sources"
    ),
)
ELECTRON_CHARGE_NUMBER: Final = -1.0
TANDEM_IDENTIFIER: Final = "tandem_mirror"


@dataclass(frozen=True, slots=True)
class TandemInputs:
    """Declared inputs of the tandem-mirror closed forms.

    Parameters
    ----------
    plug_density_per_m3
        End-plug density ``n_p``; strictly positive.
    central_ion_temperature_kev
        Central-cell ion temperature ``T_ic``; strictly positive.
    plug_electron_potential_kev
        Declared plug electron-confining potential ``phi_e``; strictly
        positive.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or not strictly positive.
    """

    plug_density_per_m3: float
    central_ion_temperature_kev: float
    plug_electron_potential_kev: float

    def __post_init__(self) -> None:
        """Validate every declared input.

        Raises
        ------
        DeviceConfigurationError
            If any input is non-finite or not strictly positive.
        """
        require_positive("plug_density_per_m3", self.plug_density_per_m3)
        require_positive(
            "central_ion_temperature_kev", self.central_ion_temperature_kev
        )
        require_positive(
            "plug_electron_potential_kev", self.plug_electron_potential_kev
        )

    def to_record(self) -> dict[str, Any]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "plug_density_per_m3": self.plug_density_per_m3,
            "central_ion_temperature_kev": self.central_ion_temperature_kev,
            "plug_electron_potential_kev": self.plug_electron_potential_kev,
        }


@dataclass(frozen=True, slots=True)
class ModelInputs:
    """Declared inputs of the level-0 models beyond the configuration.

    Parameters
    ----------
    midplane_beta
        ``beta`` in ``[0, 1)``.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    ion_charge_number
        Ion charge ``Z``; strictly positive.
    density_per_m3
        Plasma density (the central-cell density of a tandem); strictly
        positive.
    electron_temperature_kev
        ``T_e``; strictly positive.
    ion_energy_kev
        Ion (beam) energy ``E_i``; strictly positive.
    plasma_radius_m
        Plasma radius ``a``; strictly positive.
    potential_drop_kev
        ``phi_0 - phi_throat`` in kilovolts; non-negative.
    parallel_velocity_fraction
        ``v_par / v`` of the ion population in ``[0, 1]``.
    field_gradient_scale_length_m
        ``L_B``; strictly positive.
    tandem
        Tandem inputs; required exactly for ``tandem_mirror``.

    Raises
    ------
    DeviceConfigurationError
        If any input is invalid.
    """

    midplane_beta: float
    ion_mass_amu: float
    ion_charge_number: float
    density_per_m3: float
    electron_temperature_kev: float
    ion_energy_kev: float
    plasma_radius_m: float
    potential_drop_kev: float
    parallel_velocity_fraction: float
    field_gradient_scale_length_m: float
    tandem: TandemInputs | None = None

    def __post_init__(self) -> None:
        """Validate every declared input.

        Raises
        ------
        DeviceConfigurationError
            If any input is invalid.
        """
        require_midplane_beta(self.midplane_beta)
        require_positive("ion_mass_amu", self.ion_mass_amu)
        require_positive("ion_charge_number", self.ion_charge_number)
        require_positive("density_per_m3", self.density_per_m3)
        require_positive("electron_temperature_kev", self.electron_temperature_kev)
        require_positive("ion_energy_kev", self.ion_energy_kev)
        require_positive("plasma_radius_m", self.plasma_radius_m)
        require_finite("potential_drop_kev", self.potential_drop_kev)
        if self.potential_drop_kev < 0.0:
            raise DeviceConfigurationError(
                "potential_drop_kev: must be non-negative, got "
                f"{self.potential_drop_kev!r}"
            )
        require_fraction("parallel_velocity_fraction", self.parallel_velocity_fraction)
        require_positive(
            "field_gradient_scale_length_m", self.field_gradient_scale_length_m
        )

    def to_record(self) -> dict[str, Any]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name; ``tandem`` is ``None`` or its record.
        """
        return {
            "midplane_beta": self.midplane_beta,
            "ion_mass_amu": self.ion_mass_amu,
            "ion_charge_number": self.ion_charge_number,
            "density_per_m3": self.density_per_m3,
            "electron_temperature_kev": self.electron_temperature_kev,
            "ion_energy_kev": self.ion_energy_kev,
            "plasma_radius_m": self.plasma_radius_m,
            "potential_drop_kev": self.potential_drop_kev,
            "parallel_velocity_fraction": self.parallel_velocity_fraction,
            "field_gradient_scale_length_m": self.field_gradient_scale_length_m,
            "tandem": None if self.tandem is None else self.tandem.to_record(),
        }


@dataclass(frozen=True, slots=True)
class Level0PhysicsRecord:
    """The level-0 models evaluated on one configuration.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the record was built from.
    inputs
        Declared model inputs.
    plasma_half_length_m
        Half the central-cell length.
    mirror
        Vacuum and diamagnetic mirror ratios.
    ion_loss_boundary
        Loss boundary of the ions at ``E_i``.
    electron_loss_boundary
        Loss boundary of the electrons at ``T_e``.
    collisions
        Collisional time scales.
    confinement
        Confinement scalings and the regime disposition.
    flr
        FLR interchange criterion.
    adiabaticity
        Fast-ion adiabaticity parameter.
    tandem
        Tandem confinement; ``None`` unless the configuration is a tandem.
    """

    configuration_digest_sha256: str
    inputs: ModelInputs
    plasma_half_length_m: float
    mirror: MirrorRatio
    ion_loss_boundary: LossBoundary
    electron_loss_boundary: LossBoundary
    collisions: CollisionTimes
    confinement: ConfinementScalings
    flr: FlrCriterion
    adiabaticity: Adiabaticity
    tandem: TandemConfinement | None

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            Schema identity, non-claims, and every model record.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "non_claims": list(LEVEL0_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "inputs": self.inputs.to_record(),
            "plasma_half_length_m": self.plasma_half_length_m,
            "mirror": self.mirror.to_record(),
            "ion_loss_boundary": self.ion_loss_boundary.to_record(),
            "electron_loss_boundary": self.electron_loss_boundary.to_record(),
            "collisions": self.collisions.to_record(),
            "confinement": self.confinement.to_record(),
            "flr": self.flr.to_record(),
            "adiabaticity": self.adiabaticity.to_record(),
            "tandem": None if self.tandem is None else self.tandem.to_record(),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(
    configuration: DeviceConfiguration, inputs: ModelInputs
) -> Level0PhysicsRecord:
    """Evaluate every level-0 model on a validated configuration.

    Parameters
    ----------
    configuration
        Validated mirror configuration.
    inputs
        Declared model inputs.

    Returns
    -------
    Level0PhysicsRecord
        The composed record.

    Raises
    ------
    DeviceConfigurationError
        If the tandem inputs are missing for a tandem mirror or present for
        another class, or any model refuses its inputs.
    """
    is_tandem = configuration.identifier == TANDEM_IDENTIFIER
    if is_tandem and inputs.tandem is None:
        raise DeviceConfigurationError(
            "tandem: tandem_mirror requires the tandem inputs (plug density, "
            "central ion temperature, plug electron potential)"
        )
    if not is_tandem and inputs.tandem is not None:
        raise DeviceConfigurationError(
            f"tandem: {configuration.identifier} carries no end plugs; tandem "
            "inputs must be None"
        )
    half_length = configuration.layout.central_cell_length_m / 2.0
    field_t = configuration.field.b_min_t
    ratio = mirror_ratio(configuration, inputs.midplane_beta)
    ions = loss_boundary(
        ratio.effective_ratio,
        inputs.ion_charge_number,
        inputs.ion_energy_kev,
        inputs.potential_drop_kev,
    )
    electrons = loss_boundary(
        ratio.effective_ratio,
        ELECTRON_CHARGE_NUMBER,
        inputs.electron_temperature_kev,
        inputs.potential_drop_kev,
    )
    collisions = collision_times(
        inputs.density_per_m3,
        inputs.electron_temperature_kev,
        inputs.ion_energy_kev,
        inputs.ion_mass_amu,
        inputs.ion_charge_number,
    )
    confinement = confinement_scalings(
        ratio.effective_ratio,
        half_length,
        inputs.density_per_m3,
        inputs.electron_temperature_kev,
        inputs.ion_energy_kev,
        inputs.ion_mass_amu,
        collisional_regime=configuration.collisional_regime,
    )
    flr = flr_criterion(
        inputs.plasma_radius_m,
        half_length,
        inputs.ion_energy_kev,
        inputs.ion_mass_amu,
        inputs.ion_charge_number,
        field_t,
    )
    adiabatic = adiabaticity(
        inputs.field_gradient_scale_length_m,
        inputs.parallel_velocity_fraction,
        inputs.ion_energy_kev,
        inputs.ion_mass_amu,
        inputs.ion_charge_number,
        field_t,
    )
    tandem = None
    if inputs.tandem is not None:
        tandem = tandem_confinement(
            ratio.effective_ratio,
            inputs.tandem.plug_density_per_m3,
            inputs.density_per_m3,
            inputs.electron_temperature_kev,
            inputs.tandem.central_ion_temperature_kev,
            inputs.ion_mass_amu,
            inputs.ion_charge_number,
            field_t,
            configuration.layout.central_cell_length_m,
            inputs.plasma_radius_m,
            inputs.tandem.plug_electron_potential_kev,
            inputs.parallel_velocity_fraction,
        )
    return Level0PhysicsRecord(
        configuration_digest_sha256=configuration.digest_sha256(),
        inputs=inputs,
        plasma_half_length_m=half_length,
        mirror=ratio,
        ion_loss_boundary=ions,
        electron_loss_boundary=electrons,
        collisions=collisions,
        confinement=confinement,
        flr=flr,
        adiabaticity=adiabatic,
        tandem=tandem,
    )
