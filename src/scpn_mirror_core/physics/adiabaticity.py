# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — fast-ion adiabaticity parameter

"""Fast-ion adiabaticity parameter in the published form.

D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501, section 3.6
(after Cohen, Rowlands & Foote 1978b): the first adiabatic invariant fails
when a particle sees a large change of field strength in one gyro-period,
measured by ``alpha = L_B / rho_par`` with ``rho_par = v_par / omega_ci``
and ``L_B = |B| / |grad B|``; the source states that non-adiabatic effects
become significant at ``alpha <= 10``. The gradient scale length is a
declared input at level 0 (a field model belongs to level 2); the parallel
speed is the declared fraction of ``sqrt(2 E_i / m_i)``. A zero fraction
has no parallel gyroradius and is reported as not applicable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import require_finite, require_positive
from scpn_mirror_core.physics.stability import ion_gyromotion

ADIABATICITY_THRESHOLD = 10.0


def require_fraction(name: str, value: float) -> float:
    """Return ``value`` when it lies in ``[0, 1]``.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated fraction.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or outside ``[0, 1]``.
    """
    require_finite(name, value)
    if not 0.0 <= value <= 1.0:
        raise DeviceConfigurationError(f"{name}: must lie in [0, 1], got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class Adiabaticity:
    """Adiabaticity parameter of one ion population.

    Parameters
    ----------
    parallel_speed_m_s
        ``f sqrt(2 E_i / m_i)``.
    parallel_gyroradius_m
        ``v_par / omega_ci``; ``None`` when the fraction is zero.
    alpha
        ``L_B / rho_par``; ``None`` when not applicable.
    adiabatic
        ``alpha > 10``; ``None`` when not applicable.
    """

    parallel_speed_m_s: float
    parallel_gyroradius_m: float | None
    alpha: float | None
    adiabatic: bool | None

    def to_record(self) -> dict[str, Any]:
        """Project the parameter to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "parallel_speed_m_s": self.parallel_speed_m_s,
            "parallel_gyroradius_m": self.parallel_gyroradius_m,
            "alpha": self.alpha,
            "adiabatic": self.adiabatic,
        }


def adiabaticity(
    field_gradient_scale_length_m: float,
    parallel_velocity_fraction: float,
    ion_energy_kev: float,
    ion_mass_amu: float,
    charge_number: float,
    field_t: float,
) -> Adiabaticity:
    """Evaluate the adiabaticity parameter.

    Parameters
    ----------
    field_gradient_scale_length_m
        ``L_B``; strictly positive.
    parallel_velocity_fraction
        ``v_par / v`` in ``[0, 1]``.
    ion_energy_kev
        Ion energy; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.
    field_t
        Field where the parameter is evaluated; strictly positive.

    Returns
    -------
    Adiabaticity
        The parameter and its disposition.

    Raises
    ------
    DeviceConfigurationError
        If an input is invalid.
    """
    require_positive("field_gradient_scale_length_m", field_gradient_scale_length_m)
    fraction = require_fraction(
        "parallel_velocity_fraction", parallel_velocity_fraction
    )
    require_positive("ion_energy_kev", ion_energy_kev)
    require_positive("ion_mass_amu", ion_mass_amu)
    require_positive("charge_number", charge_number)
    require_positive("field_t", field_t)
    speed, frequency, _ = ion_gyromotion(
        ion_energy_kev, ion_mass_amu, charge_number, field_t
    )
    parallel_speed = fraction * speed
    if fraction == 0.0:
        return Adiabaticity(
            parallel_speed_m_s=parallel_speed,
            parallel_gyroradius_m=None,
            alpha=None,
            adiabatic=None,
        )
    parallel_gyroradius = parallel_speed / frequency
    alpha = field_gradient_scale_length_m / parallel_gyroradius
    return Adiabaticity(
        parallel_speed_m_s=parallel_speed,
        parallel_gyroradius_m=parallel_gyroradius,
        alpha=alpha,
        adiabatic=alpha > ADIABATICITY_THRESHOLD,
    )
