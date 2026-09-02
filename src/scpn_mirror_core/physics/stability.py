# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — finite-Larmor-radius interchange criterion

"""FLR stabilisation of interchange modes in the published form.

D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501, eq. 3.7 (from
Ryutov et al. 2011): azimuthal modes ``m > 2 a^2 / (L_p rho_i)`` are
stabilised by finite-Larmor-radius effects, with ``a`` the plasma radius,
``L_p`` the plasma half-length and ``rho_i`` the ion gyroradius, which is
evaluated here as ``m_i v / (Z e B_0)`` with ``v = sqrt(2 E_i / m_i)`` at
the midplane field (the source leaves ``rho_i`` as "the ion gyroradius").
The source's worked case ``a / rho_i = 4``, ``L_p / a = 10`` gives
``m_crit = 0.8`` ("all modes with m >= 2 should be FLR stabilised"). The
``m = 1`` mode is not assessed at level 0: the vortex and sheared-flow
conditions (eqs. 3.8-3.9) need a field-curvature scale length.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.parameters import require_positive
from scpn_mirror_core.physics.numerics import ATOMIC_MASS_KG, ELEMENTARY_CHARGE_C, KEV_J

FLR_MODE_THRESHOLD = 2.0


@dataclass(frozen=True, slots=True)
class FlrCriterion:
    """FLR interchange criterion of Endrizzi eq. 3.7.

    Parameters
    ----------
    ion_speed_m_s
        ``sqrt(2 E_i / m_i)``.
    cyclotron_frequency_rad_s
        ``Z e B_0 / m_i``.
    ion_gyroradius_m
        ``v / omega_ci``.
    critical_mode_number
        ``2 a^2 / (L_p rho_i)``.
    m2_stabilised
        ``True`` when every ``m >= 2`` exceeds the critical number.
    """

    ion_speed_m_s: float
    cyclotron_frequency_rad_s: float
    ion_gyroradius_m: float
    critical_mode_number: float
    m2_stabilised: bool

    def to_record(self) -> dict[str, Any]:
        """Project the criterion to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "ion_speed_m_s": self.ion_speed_m_s,
            "cyclotron_frequency_rad_s": self.cyclotron_frequency_rad_s,
            "ion_gyroradius_m": self.ion_gyroradius_m,
            "critical_mode_number": self.critical_mode_number,
            "m2_stabilised": self.m2_stabilised,
        }


def ion_gyromotion(
    ion_energy_kev: float, ion_mass_amu: float, charge_number: float, field_t: float
) -> tuple[float, float, float]:
    """Return ``(v, omega_ci, rho_i)`` of an ion at the given field.

    Parameters
    ----------
    ion_energy_kev
        Ion kinetic energy; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.
    field_t
        Magnetic field; strictly positive.

    Returns
    -------
    (float, float, float)
        Speed, cyclotron frequency and gyroradius.
    """
    ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG
    speed = math.sqrt(2.0 * ion_energy_kev * KEV_J / ion_mass_kg)
    frequency = charge_number * ELEMENTARY_CHARGE_C * field_t / ion_mass_kg
    return speed, frequency, speed / frequency


def critical_mode_number(
    plasma_radius_m: float, plasma_half_length_m: float, ion_gyroradius_m: float
) -> float:
    """Return ``2 a^2 / (L_p rho_i)`` of Endrizzi eq. 3.7.

    Parameters
    ----------
    plasma_radius_m
        Plasma radius ``a``; strictly positive.
    plasma_half_length_m
        Plasma half-length ``L_p``; strictly positive.
    ion_gyroradius_m
        Ion gyroradius; strictly positive.

    Returns
    -------
    float
        The critical azimuthal mode number.

    Raises
    ------
    DeviceConfigurationError
        If any input is not strictly positive.
    """
    require_positive("plasma_radius_m", plasma_radius_m)
    require_positive("plasma_half_length_m", plasma_half_length_m)
    require_positive("ion_gyroradius_m", ion_gyroradius_m)
    return (
        2.0
        * plasma_radius_m
        * plasma_radius_m
        / (plasma_half_length_m * ion_gyroradius_m)
    )


def flr_criterion(
    plasma_radius_m: float,
    plasma_half_length_m: float,
    ion_energy_kev: float,
    ion_mass_amu: float,
    charge_number: float,
    field_t: float,
) -> FlrCriterion:
    """Evaluate the FLR interchange criterion.

    Parameters
    ----------
    plasma_radius_m
        Plasma radius ``a``; strictly positive.
    plasma_half_length_m
        Plasma half-length ``L_p``; strictly positive.
    ion_energy_kev
        Ion energy; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.
    field_t
        Midplane field ``B_0``; strictly positive.

    Returns
    -------
    FlrCriterion
        Gyromotion quantities, the critical mode number and the disposition.

    Raises
    ------
    DeviceConfigurationError
        If any input is not strictly positive.
    """
    require_positive("ion_energy_kev", ion_energy_kev)
    require_positive("ion_mass_amu", ion_mass_amu)
    require_positive("charge_number", charge_number)
    require_positive("field_t", field_t)
    speed, frequency, gyroradius = ion_gyromotion(
        ion_energy_kev, ion_mass_amu, charge_number, field_t
    )
    critical = critical_mode_number(plasma_radius_m, plasma_half_length_m, gyroradius)
    return FlrCriterion(
        ion_speed_m_s=speed,
        cyclotron_frequency_rad_s=frequency,
        ion_gyroradius_m=gyroradius,
        critical_mode_number=critical,
        m2_stabilised=critical < FLR_MODE_THRESHOLD,
    )
