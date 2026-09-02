# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — tandem-mirror confinement closed forms

"""Tandem-mirror confinement in the published closed forms.

S. Frank et al., J. Plasma Phys. 91 (2025) E110, section 3: the ion
confining potential ``phi_i = T_e ln(n_p / n_c)`` (eq. 3.4); the function
``G(x) = sqrt(1 + 1/x) ln((sqrt(1 + 1/x) + 1) / (sqrt(1 + 1/x) - 1))`` of
the central-cell mirror ratio (eq. 3.5); the Pastukhov confinement
``tau_Past = (sqrt(pi) / 2) tau_ii (phi_i / T_ic) exp(phi_i / T_ic)
G(R_mc) / (1 + T_ic / (2 phi_i) - (T_ic / (2 phi_i))^2)`` (eq. 3.3;
Pastukhov 1974, Cohen et al. 1978); the collisional-trapping time
``tau_f = sqrt(pi) R_mc (l_c / v_thic) exp(phi_i / T_ic)`` with
``v_thic = sqrt(T_ic / (2 m_ic))`` (eq. 3.6; Rognlien & Cutler 1980); the
classical radial time ``tau_rho = 0.25 (a_c / rho_ic)^2 tau_ii`` with
``rho_ic = v_thic / Omega_ic`` (eq. 3.7); the combined
``tau_c = (1 / (tau_Past + tau_f) + 1 / tau_rho)^(-1)`` (eq. 3.2); and the
ambipolar-hole loss energy ``E_h = phi_e / (R_m sin^2 theta_NBI - 1)``
(eq. 4.3) with the plug electron-confining potential ``phi_e`` declared,
because eq. 3.8 (which fixes it) is a transcendental equation and level 0
solves no equation. ``tau_ii`` is the central-cell ion-ion scattering time
of Endrizzi et al. eq. 3.2 evaluated at ``E_i = T_ic`` (a declared
modelling choice). The transcendental functions are the shared library's.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import require_positive
from scpn_mirror_core.physics.collisions import ion_scattering_time
from scpn_mirror_core.physics.numerics import (
    ATOMIC_MASS_KG,
    ELEMENTARY_CHARGE_C,
    KEV_J,
    PI,
    exponential,
    natural_log,
)


@dataclass(frozen=True, slots=True)
class TandemConfinement:
    """Tandem-mirror confinement quantities (SI in the names).

    Parameters
    ----------
    ion_confining_potential_kev
        ``phi_i`` of eq. 3.4.
    potential_ratio
        ``phi_i / T_ic``.
    pastukhov_function
        ``G(R_mc)`` of eq. 3.5.
    ion_scattering_time_s
        ``tau_ii`` at ``E_i = T_ic``.
    pastukhov_time_s
        ``tau_Past`` of eq. 3.3.
    ion_thermal_speed_m_s
        ``v_thic``.
    trapping_time_s
        ``tau_f`` of eq. 3.6.
    ion_gyroradius_m
        ``rho_ic``.
    radial_time_s
        ``tau_rho`` of eq. 3.7.
    combined_time_s
        ``tau_c`` of eq. 3.2.
    hole_denominator
        ``R_m sin^2 theta_NBI - 1``.
    ambipolar_hole_energy_kev
        ``E_h`` of eq. 4.3; ``None`` when the denominator is not positive.
    """

    ion_confining_potential_kev: float
    potential_ratio: float
    pastukhov_function: float
    ion_scattering_time_s: float
    pastukhov_time_s: float
    ion_thermal_speed_m_s: float
    trapping_time_s: float
    ion_gyroradius_m: float
    radial_time_s: float
    combined_time_s: float
    hole_denominator: float
    ambipolar_hole_energy_kev: float | None

    def to_record(self) -> dict[str, Any]:
        """Project the quantities to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "ion_confining_potential_kev": self.ion_confining_potential_kev,
            "potential_ratio": self.potential_ratio,
            "pastukhov_function": self.pastukhov_function,
            "ion_scattering_time_s": self.ion_scattering_time_s,
            "pastukhov_time_s": self.pastukhov_time_s,
            "ion_thermal_speed_m_s": self.ion_thermal_speed_m_s,
            "trapping_time_s": self.trapping_time_s,
            "ion_gyroradius_m": self.ion_gyroradius_m,
            "radial_time_s": self.radial_time_s,
            "combined_time_s": self.combined_time_s,
            "hole_denominator": self.hole_denominator,
            "ambipolar_hole_energy_kev": self.ambipolar_hole_energy_kev,
        }


def pastukhov_function(mirror_ratio: float) -> float:
    """Return ``G(x)`` of Frank eq. 3.5.

    Parameters
    ----------
    mirror_ratio
        Central-cell mirror ratio ``x``; strictly positive.

    Returns
    -------
    float
        ``sqrt(1 + 1/x) ln((sqrt(1 + 1/x) + 1) / (sqrt(1 + 1/x) - 1))``.
    """
    require_positive("mirror_ratio", mirror_ratio)
    root = math.sqrt(1.0 + 1.0 / mirror_ratio)
    return root * natural_log((root + 1.0) / (root - 1.0))


def tandem_confinement(
    effective_ratio: float,
    plug_density_per_m3: float,
    central_density_per_m3: float,
    electron_temperature_kev: float,
    central_ion_temperature_kev: float,
    ion_mass_amu: float,
    charge_number: float,
    central_field_t: float,
    central_cell_length_m: float,
    plasma_radius_m: float,
    plug_electron_potential_kev: float,
    parallel_velocity_fraction: float,
) -> TandemConfinement:
    """Evaluate the tandem-mirror confinement closed forms.

    Parameters
    ----------
    effective_ratio
        Central-cell mirror ratio ``R_mc``; strictly positive.
    plug_density_per_m3
        End-plug density ``n_p``; strictly larger than the central density.
    central_density_per_m3
        Central-cell density ``n_c``; strictly positive.
    electron_temperature_kev
        ``T_e``; strictly positive.
    central_ion_temperature_kev
        ``T_ic``; strictly positive.
    ion_mass_amu
        Ion mass in proton masses; strictly positive.
    charge_number
        Ion charge ``Z``; strictly positive.
    central_field_t
        Central-cell midplane field ``B_0c``; strictly positive.
    central_cell_length_m
        ``l_c``; strictly positive.
    plasma_radius_m
        ``a_c``; strictly positive.
    plug_electron_potential_kev
        Declared ``phi_e``; strictly positive.
    parallel_velocity_fraction
        ``cos theta_NBI`` of the injected ions in ``[0, 1]``.

    Returns
    -------
    TandemConfinement
        Every quantity of eqs. 3.2-3.7 and 4.3.

    Raises
    ------
    DeviceConfigurationError
        If an input is invalid, or the plug density does not exceed the
        central density (the ion confining potential would not be
        positive and the Pastukhov form does not apply).
    NumericsError
        If the exponential of ``phi_i / T_ic`` leaves the library's window.
    """
    require_positive("effective_ratio", effective_ratio)
    require_positive("plug_density_per_m3", plug_density_per_m3)
    require_positive("central_density_per_m3", central_density_per_m3)
    require_positive("electron_temperature_kev", electron_temperature_kev)
    require_positive("central_ion_temperature_kev", central_ion_temperature_kev)
    require_positive("ion_mass_amu", ion_mass_amu)
    require_positive("charge_number", charge_number)
    require_positive("central_field_t", central_field_t)
    require_positive("central_cell_length_m", central_cell_length_m)
    require_positive("plasma_radius_m", plasma_radius_m)
    require_positive("plug_electron_potential_kev", plug_electron_potential_kev)
    if plug_density_per_m3 <= central_density_per_m3:
        raise DeviceConfigurationError(
            "plug_density_per_m3: must exceed central_density_per_m3 for a positive "
            f"ion confining potential, got {plug_density_per_m3!r} <= "
            f"{central_density_per_m3!r}"
        )
    potential = electron_temperature_kev * natural_log(
        plug_density_per_m3 / central_density_per_m3
    )
    ratio = potential / central_ion_temperature_kev
    function = pastukhov_function(effective_ratio)
    scattering = ion_scattering_time(
        central_density_per_m3, central_ion_temperature_kev, ion_mass_amu, charge_number
    )
    half = central_ion_temperature_kev / (2.0 * potential)
    growth = exponential(ratio)
    pastukhov = ((math.sqrt(PI) / 2.0) * scattering * ratio * growth * function) / (
        1.0 + half - half * half
    )
    ion_mass_kg = ion_mass_amu * ATOMIC_MASS_KG
    thermal_speed = math.sqrt(central_ion_temperature_kev * KEV_J / (2.0 * ion_mass_kg))
    trapping = (
        math.sqrt(PI)
        * effective_ratio
        * (central_cell_length_m / thermal_speed)
        * growth
    )
    cyclotron = charge_number * ELEMENTARY_CHARGE_C * central_field_t / ion_mass_kg
    gyroradius = thermal_speed / cyclotron
    radial_ratio = plasma_radius_m / gyroradius
    radial = 0.25 * (radial_ratio * radial_ratio) * scattering
    combined = 1.0 / (1.0 / (pastukhov + trapping) + 1.0 / radial)
    sine_squared = 1.0 - parallel_velocity_fraction * parallel_velocity_fraction
    denominator = effective_ratio * sine_squared - 1.0
    hole = plug_electron_potential_kev / denominator if denominator > 0.0 else None
    return TandemConfinement(
        ion_confining_potential_kev=potential,
        potential_ratio=ratio,
        pastukhov_function=function,
        ion_scattering_time_s=scattering,
        pastukhov_time_s=pastukhov,
        ion_thermal_speed_m_s=thermal_speed,
        trapping_time_s=trapping,
        ion_gyroradius_m=gyroradius,
        radial_time_s=radial,
        combined_time_s=combined,
        hole_denominator=denominator,
        ambipolar_hole_energy_kev=hole,
    )
