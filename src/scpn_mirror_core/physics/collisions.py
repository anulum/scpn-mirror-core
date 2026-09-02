# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — collisional time scales

"""Collisional time scales of a mirror plasma in the published engineering forms.

D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501, eqs. 3.1-3.3:
``n20 tau_s = 5 T_e,keV^(3/2) mu / Z^2 ms`` (slowing of fast ions on
electrons), ``n20 tau_ii = E_i,keV^(3/2) mu / (8 Z^2) ms`` (ion-ion
pitch-angle scattering) and ``n20 tau_ee = 5.8 T_e,keV^(3/2) us``
(electron-electron), with ``n20`` the density in ``1e20 m^-3``, ``mu`` the
ion mass in proton masses and ``Z`` the ion charge. The source states that
the first two are equal when ``T_e = E_i / 40^(2/3)``; that temperature
is reported so the identity can be tested. ``x^(3/2)`` is evaluated as
``x sqrt(x)``; ``40^(2/3)`` by the library's power kernel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.parameters import require_positive
from scpn_mirror_core.physics.numerics import power

MILLISECOND_S = 1.0e-3
MICROSECOND_S = 1.0e-6
DENSITY_UNIT_PER_M3 = 1.0e20


@dataclass(frozen=True, slots=True)
class CollisionTimes:
    """Collisional time scales at one operating point (seconds).

    Parameters
    ----------
    density_unit
        ``n / 1e20 m^-3``.
    slowing_time_s
        ``tau_s`` of eq. 3.1.
    ion_scattering_time_s
        ``tau_ii`` of eq. 3.2.
    electron_scattering_time_s
        ``tau_ee`` of eq. 3.3.
    equal_time_electron_temperature_kev
        ``E_i / 40^(2/3)``, where ``tau_s = tau_ii``.
    """

    density_unit: float
    slowing_time_s: float
    ion_scattering_time_s: float
    electron_scattering_time_s: float
    equal_time_electron_temperature_kev: float

    def to_record(self) -> dict[str, Any]:
        """Project the times to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "density_unit": self.density_unit,
            "slowing_time_s": self.slowing_time_s,
            "ion_scattering_time_s": self.ion_scattering_time_s,
            "electron_scattering_time_s": self.electron_scattering_time_s,
            "equal_time_electron_temperature_kev": (
                self.equal_time_electron_temperature_kev
            ),
        }


def three_halves(x: float) -> float:
    """Return ``x^(3/2)`` as ``x sqrt(x)``.

    Parameters
    ----------
    x
        Non-negative argument.

    Returns
    -------
    float
        ``x * sqrt(x)``.
    """
    return x * math.sqrt(x)


def ion_scattering_time(
    density_per_m3: float,
    ion_energy_kev: float,
    ion_mass_amu: float,
    charge_number: float,
) -> float:
    """Return ``tau_ii`` of Endrizzi eq. 3.2 in seconds.

    Parameters
    ----------
    density_per_m3
        Plasma density; strictly positive.
    ion_energy_kev
        Ion energy ``E_i``; strictly positive.
    ion_mass_amu
        Ion mass ``mu`` in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.

    Returns
    -------
    float
        The pitch-angle scattering time.
    """
    unit = density_per_m3 / DENSITY_UNIT_PER_M3
    return (
        (
            three_halves(ion_energy_kev)
            * ion_mass_amu
            / (8.0 * charge_number * charge_number)
        )
        / unit
        * MILLISECOND_S
    )


def collision_times(
    density_per_m3: float,
    electron_temperature_kev: float,
    ion_energy_kev: float,
    ion_mass_amu: float,
    charge_number: float,
) -> CollisionTimes:
    """Evaluate the three collisional time scales.

    Parameters
    ----------
    density_per_m3
        Plasma density; strictly positive.
    electron_temperature_kev
        Electron temperature; strictly positive.
    ion_energy_kev
        Ion energy ``E_i``; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.

    Returns
    -------
    CollisionTimes
        The times in seconds and the equal-time electron temperature.

    Raises
    ------
    DeviceConfigurationError
        If any input is not strictly positive.
    """
    require_positive("density_per_m3", density_per_m3)
    require_positive("electron_temperature_kev", electron_temperature_kev)
    require_positive("ion_energy_kev", ion_energy_kev)
    require_positive("ion_mass_amu", ion_mass_amu)
    require_positive("charge_number", charge_number)
    unit = density_per_m3 / DENSITY_UNIT_PER_M3
    z_squared = charge_number * charge_number
    slowing = (
        (5.0 * three_halves(electron_temperature_kev) * ion_mass_amu / z_squared)
        / unit
        * MILLISECOND_S
    )
    ion = ion_scattering_time(
        density_per_m3, ion_energy_kev, ion_mass_amu, charge_number
    )
    electron = (5.8 * three_halves(electron_temperature_kev)) / unit * MICROSECOND_S
    equal = ion_energy_kev / power(40.0, 2.0 / 3.0)
    return CollisionTimes(
        density_unit=unit,
        slowing_time_s=slowing,
        ion_scattering_time_s=ion,
        electron_scattering_time_s=electron,
        equal_time_electron_temperature_kev=equal,
    )
