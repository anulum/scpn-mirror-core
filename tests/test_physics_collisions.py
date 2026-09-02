# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — collisional time-scale tests

"""Endrizzi eqs. 3.1-3.3, the equal-time identity and refusals."""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.physics import (
    collision_times,
    ion_scattering_time,
    power,
    three_halves,
)


def test_engineering_forms_at_unit_inputs() -> None:
    """n20 = 1, T = E = 1 keV, mu = Z = 1 give 5 ms, 1/8 ms, 5.8 us."""
    times = collision_times(1.0e20, 1.0, 1.0, 1.0, 1.0)
    assert times.density_unit == 1.0
    assert times.slowing_time_s == 5.0 * 1.0e-3
    assert times.ion_scattering_time_s == (1.0 / 8.0) * 1.0e-3
    assert times.electron_scattering_time_s == 5.8 * 1.0e-6
    assert times.equal_time_electron_temperature_kev == 1.0 / power(40.0, 2.0 / 3.0)
    assert set(times.to_record()) == {
        "density_unit",
        "slowing_time_s",
        "ion_scattering_time_s",
        "electron_scattering_time_s",
        "equal_time_electron_temperature_kev",
    }


def test_slowing_equals_scattering_at_the_stated_temperature() -> None:
    """The source: tau_s = tau_ii when T_e = E_i / 40^(2/3) (about E_i / 10)."""
    reference = collision_times(3.0e19, 1.0, 25.0, 2.0, 1.0)
    equal = reference.equal_time_electron_temperature_kev
    assert 25.0 / 12.0 < equal < 25.0 / 10.0
    times = collision_times(3.0e19, equal, 25.0, 2.0, 1.0)
    assert math.isclose(
        times.slowing_time_s, times.ion_scattering_time_s, rel_tol=1.0e-14
    )


def test_scalings_with_energy_mass_charge_and_density() -> None:
    """tau_ii ∝ E^(3/2) mu / (Z^2 n); tau_ee ∝ T^(3/2) / n."""
    base = collision_times(1.0e20, 2.0, 4.0, 2.0, 1.0)
    assert three_halves(4.0) == 8.0
    assert ion_scattering_time(1.0e20, 4.0, 2.0, 1.0) == base.ion_scattering_time_s
    assert math.isclose(
        ion_scattering_time(1.0e20, 16.0, 2.0, 1.0), 8.0 * base.ion_scattering_time_s
    )
    assert math.isclose(
        ion_scattering_time(1.0e20, 4.0, 2.0, 2.0), base.ion_scattering_time_s / 4.0
    )
    assert math.isclose(
        collision_times(2.0e20, 2.0, 4.0, 2.0, 1.0).electron_scattering_time_s,
        base.electron_scattering_time_s / 2.0,
    )


@pytest.mark.parametrize(
    "field",
    [
        "density_per_m3",
        "electron_temperature_kev",
        "ion_energy_kev",
        "ion_mass_amu",
        "charge_number",
    ],
)
def test_non_positive_inputs_are_refused(field: str) -> None:
    """Every input is strictly positive."""
    values: dict[str, Any] = {
        "density_per_m3": 1.0e20,
        "electron_temperature_kev": 1.0,
        "ion_energy_kev": 1.0,
        "ion_mass_amu": 1.0,
        "charge_number": 1.0,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        collision_times(**values)
