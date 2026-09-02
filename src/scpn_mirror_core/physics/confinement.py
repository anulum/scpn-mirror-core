# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — confinement scalings

"""Classical-mirror and gas-dynamic confinement scalings in their published forms.

D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501: eq. 3.4, the
classical (collisionless) fast-ion confinement
``n20 tau_p = 250 E_b,100keV^(3/2) log10 R_m ms`` (attributed there to
Killeen & Marx 1970, Killeen, Mirin & Rensink 1976 and Egedal et al.
2022; the coefficient depends on field shape, injection angle and
electron heating); eq. 3.5, the gas-dynamic (collisional) time
``tau_GDT = R_m L_p / c_s = 5.2 R_m L_p T_e,keV^(-1/2) us`` (attributed to
Ivanov & Prikhodko 2013). The dimensional form is evaluated with the
declared sound speed ``c_s = sqrt(T_e / m_i)`` and the printed coefficient
form alongside; for an ion mass of 2.5 proton masses the two agree to
within 3 %, which fixes the sound-speed definition the printed coefficient
implies. ``log10`` is ``ln / ln 10`` by the library kernel. The regime
disposition follows the configuration's collisional-regime declaration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.parameters import require_positive
from scpn_mirror_core.physics.collisions import (
    DENSITY_UNIT_PER_M3,
    MICROSECOND_S,
    MILLISECOND_S,
    three_halves,
)
from scpn_mirror_core.physics.numerics import ATOMIC_MASS_KG, KEV_J, natural_log

REGIME_GAS_DYNAMIC = "gas_dynamic"
REGIME_CLASSICAL = "classical"


@dataclass(frozen=True, slots=True)
class ConfinementScalings:
    """Both confinement scalings and the regime disposition (seconds).

    Parameters
    ----------
    log10_mirror_ratio
        ``log10 R_m``.
    classical_time_s
        ``tau_p`` of eq. 3.4 at the declared density.
    sound_speed_m_s
        ``sqrt(T_e / m_i)``.
    gas_dynamic_time_s
        ``R_m L_p / c_s`` (eq. 3.5, dimensional form).
    gas_dynamic_printed_time_s
        ``5.2 R_m L_p T_e,keV^(-1/2) us`` (eq. 3.5, printed coefficient).
    regime
        ``"gas_dynamic"`` or ``"classical"`` per the configuration.
    regime_time_s
        The scaling that the regime selects.
    """

    log10_mirror_ratio: float
    classical_time_s: float
    sound_speed_m_s: float
    gas_dynamic_time_s: float
    gas_dynamic_printed_time_s: float
    regime: str
    regime_time_s: float

    def to_record(self) -> dict[str, Any]:
        """Project the scalings to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "log10_mirror_ratio": self.log10_mirror_ratio,
            "classical_time_s": self.classical_time_s,
            "sound_speed_m_s": self.sound_speed_m_s,
            "gas_dynamic_time_s": self.gas_dynamic_time_s,
            "gas_dynamic_printed_time_s": self.gas_dynamic_printed_time_s,
            "regime": self.regime,
            "regime_time_s": self.regime_time_s,
        }


def classical_confinement_time(
    density_per_m3: float, ion_energy_kev: float, effective_ratio: float
) -> tuple[float, float]:
    """Return ``(log10 R_m, tau_p)`` of Endrizzi eq. 3.4.

    Parameters
    ----------
    density_per_m3
        Plasma density; strictly positive.
    ion_energy_kev
        Beam or ion energy ``E_b``; strictly positive.
    effective_ratio
        Mirror ratio ``R_m``; strictly positive.

    Returns
    -------
    (float, float)
        ``log10 R_m`` and the confinement time in seconds.
    """
    log10_ratio = natural_log(effective_ratio) / natural_log(10.0)
    unit = density_per_m3 / DENSITY_UNIT_PER_M3
    scaled = ion_energy_kev / 100.0
    return log10_ratio, (
        250.0 * three_halves(scaled) * log10_ratio
    ) / unit * MILLISECOND_S


def gas_dynamic_confinement_time(
    effective_ratio: float,
    plasma_half_length_m: float,
    electron_temperature_kev: float,
    ion_mass_amu: float,
) -> tuple[float, float, float]:
    """Return ``(c_s, tau_GDT dimensional, tau_GDT printed)`` of eq. 3.5.

    Parameters
    ----------
    effective_ratio
        Mirror ratio ``R_m``; strictly positive.
    plasma_half_length_m
        Plasma half-length ``L_p``; strictly positive.
    electron_temperature_kev
        Electron temperature; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.

    Returns
    -------
    (float, float, float)
        Sound speed in m/s and both times in seconds.
    """
    ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG
    sound_speed = math.sqrt(electron_temperature_kev * KEV_J / ion_mass_kg)
    dimensional = effective_ratio * plasma_half_length_m / sound_speed
    printed = (
        5.2
        * effective_ratio
        * plasma_half_length_m
        / math.sqrt(electron_temperature_kev)
    ) * MICROSECOND_S
    return sound_speed, dimensional, printed


def confinement_scalings(
    effective_ratio: float,
    plasma_half_length_m: float,
    density_per_m3: float,
    electron_temperature_kev: float,
    ion_energy_kev: float,
    ion_mass_amu: float,
    collisional_regime: bool,
) -> ConfinementScalings:
    """Evaluate both scalings and select the regime's time.

    Parameters
    ----------
    effective_ratio
        Mirror ratio ``R_m``; strictly positive.
    plasma_half_length_m
        Plasma half-length ``L_p``; strictly positive.
    density_per_m3
        Plasma density; strictly positive.
    electron_temperature_kev
        Electron temperature; strictly positive.
    ion_energy_kev
        Beam or ion energy; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    collisional_regime
        The configuration's declaration; selects the gas-dynamic time.

    Returns
    -------
    ConfinementScalings
        Both scalings and the disposition.

    Raises
    ------
    DeviceConfigurationError
        If any numeric input is not strictly positive.
    """
    require_positive("effective_ratio", effective_ratio)
    require_positive("plasma_half_length_m", plasma_half_length_m)
    require_positive("density_per_m3", density_per_m3)
    require_positive("electron_temperature_kev", electron_temperature_kev)
    require_positive("ion_energy_kev", ion_energy_kev)
    require_positive("ion_mass_amu", ion_mass_amu)
    log10_ratio, classical = classical_confinement_time(
        density_per_m3, ion_energy_kev, effective_ratio
    )
    sound_speed, dimensional, printed = gas_dynamic_confinement_time(
        effective_ratio, plasma_half_length_m, electron_temperature_kev, ion_mass_amu
    )
    regime = REGIME_GAS_DYNAMIC if collisional_regime else REGIME_CLASSICAL
    return ConfinementScalings(
        log10_mirror_ratio=log10_ratio,
        classical_time_s=classical,
        sound_speed_m_s=sound_speed,
        gas_dynamic_time_s=dimensional,
        gas_dynamic_printed_time_s=printed,
        regime=regime,
        regime_time_s=dimensional if collisional_regime else classical,
    )
