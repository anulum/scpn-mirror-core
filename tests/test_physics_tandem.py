# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — tandem confinement tests

"""Frank eqs. 3.2-3.7 and 4.3: identities, dispositions and refusals."""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError, NumericsError
from scpn_mirror_core.physics import (
    ion_scattering_time,
    natural_log,
    pastukhov_function,
    tandem_confinement,
)


def arguments(**overrides: Any) -> dict[str, Any]:
    """Return the synthetic tandem arguments with optional overrides."""
    values: dict[str, Any] = {
        "effective_ratio": 20.0,
        "plug_density_per_m3": 5.0e20,
        "central_density_per_m3": 1.0e20,
        "electron_temperature_kev": 5.0,
        "central_ion_temperature_kev": 10.0,
        "ion_mass_amu": 2.5,
        "charge_number": 1.0,
        "central_field_t": 0.86,
        "central_cell_length_m": 10.0,
        "plasma_radius_m": 0.2,
        "plug_electron_potential_kev": 30.0,
        "parallel_velocity_fraction": 0.7,
    }
    values.update(overrides)
    return values


def test_pastukhov_function_closed_form_and_monotony() -> None:
    """G(1) = sqrt 2 ln(3 + 2 sqrt 2); G grows with the ratio."""
    expected = math.sqrt(2.0) * natural_log(3.0 + 2.0 * math.sqrt(2.0))
    assert math.isclose(pastukhov_function(1.0), expected, rel_tol=1.0e-14)
    values = [pastukhov_function(x) for x in (1.0, 2.0, 5.0, 20.0, 100.0)]
    assert values == sorted(values)


def test_potential_scattering_and_combination_identities() -> None:
    """phi_i = T_e ln(n_p / n_c); tau_ii at T_ic; tau_c below both channels."""
    result = tandem_confinement(**arguments())
    assert result.ion_confining_potential_kev == 5.0 * natural_log(5.0)
    assert result.potential_ratio == result.ion_confining_potential_kev / 10.0
    assert result.ion_scattering_time_s == ion_scattering_time(1.0e20, 10.0, 2.5, 1.0)
    assert result.pastukhov_function == pastukhov_function(20.0)
    assert result.combined_time_s < result.pastukhov_time_s + result.trapping_time_s
    assert result.combined_time_s < result.radial_time_s
    assert math.isclose(
        1.0 / result.combined_time_s,
        1.0 / (result.pastukhov_time_s + result.trapping_time_s)
        + 1.0 / result.radial_time_s,
        rel_tol=1.0e-14,
    )
    assert result.hole_denominator == 20.0 * (1.0 - 0.7 * 0.7) - 1.0
    assert result.ambipolar_hole_energy_kev == 30.0 / result.hole_denominator
    assert set(result.to_record()) == {
        "ion_confining_potential_kev",
        "potential_ratio",
        "pastukhov_function",
        "ion_scattering_time_s",
        "pastukhov_time_s",
        "ion_thermal_speed_m_s",
        "trapping_time_s",
        "ion_gyroradius_m",
        "radial_time_s",
        "combined_time_s",
        "hole_denominator",
        "ambipolar_hole_energy_kev",
    }


def test_hole_energy_is_absent_when_the_denominator_is_not_positive() -> None:
    """R_m sin^2 theta <= 1 has no ambipolar-hole energy (eq. 4.3 inapplicable)."""
    result = tandem_confinement(**arguments(effective_ratio=1.5))
    assert result.hole_denominator <= 0.0
    assert result.ambipolar_hole_energy_kev is None
    assert result.to_record()["ambipolar_hole_energy_kev"] is None


def test_plug_density_must_exceed_the_central_density() -> None:
    """A non-positive ion confining potential is refused, never evaluated."""
    with pytest.raises(DeviceConfigurationError, match="plug_density_per_m3"):
        tandem_confinement(**arguments(plug_density_per_m3=1.0e20))


def test_exponential_overflow_is_a_numerics_refusal() -> None:
    """A potential ratio beyond the library's window is refused, not clamped."""
    with pytest.raises(NumericsError):
        tandem_confinement(**arguments(central_ion_temperature_kev=1.0e-3))


@pytest.mark.parametrize(
    "field",
    [
        "effective_ratio",
        "plug_density_per_m3",
        "central_density_per_m3",
        "electron_temperature_kev",
        "central_ion_temperature_kev",
        "ion_mass_amu",
        "charge_number",
        "central_field_t",
        "central_cell_length_m",
        "plasma_radius_m",
        "plug_electron_potential_kev",
    ],
)
def test_non_positive_inputs_are_refused(field: str) -> None:
    """Every numeric input is strictly positive."""
    with pytest.raises(DeviceConfigurationError, match=field):
        tandem_confinement(**arguments(**{field: 0.0}))


def test_pastukhov_function_refuses_a_non_positive_ratio() -> None:
    """G needs a strictly positive ratio."""
    with pytest.raises(DeviceConfigurationError, match="mirror_ratio"):
        pastukhov_function(0.0)
