# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — confinement scaling tests

"""Endrizzi eqs. 3.4 and 3.5, the beta-gain anchor and the coefficient check."""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.physics import (
    ATOMIC_MASS_KG,
    KEV_J,
    REGIME_CLASSICAL,
    REGIME_GAS_DYNAMIC,
    classical_confinement_time,
    confinement_scalings,
    gas_dynamic_confinement_time,
    natural_log,
)


def test_classical_scaling_at_the_reference_point() -> None:
    """n20 = 1, E_b = 100 keV, R_m = 10 give exactly 250 ms."""
    log10_ratio, time_s = classical_confinement_time(1.0e20, 100.0, 10.0)
    assert log10_ratio == natural_log(10.0) / natural_log(10.0)
    assert time_s == 250.0 * 1.0e-3


def test_beta_gain_from_zero_to_nine_tenths_is_one_half_at_ratio_ten() -> None:
    """The source: 'from beta = 0 to 0.9 the gain in ntau is only 50 %'."""
    _, base = classical_confinement_time(1.0e20, 100.0, 10.0)
    _, raised = classical_confinement_time(1.0e20, 100.0, 10.0 / math.sqrt(1.0 - 0.9))
    assert math.isclose(raised / base, 1.5, rel_tol=1.0e-14)


def test_gas_dynamic_dimensional_form_and_printed_coefficient() -> None:
    """R_m L_p / c_s with c_s = sqrt(T_e / m_i); printed 5.2 within 3 % at mu 2.5."""
    sound_speed, dimensional, printed = gas_dynamic_confinement_time(1.0, 1.0, 1.0, 2.5)
    assert sound_speed == math.sqrt(KEV_J / (2.5 * ATOMIC_MASS_KG))
    assert dimensional == 1.0 / sound_speed
    assert printed == 5.2 * 1.0e-6
    assert abs(dimensional / printed - 1.0) <= 0.03
    assert 5.0e-6 < dimensional < 5.2e-6


def test_regime_disposition_follows_the_declaration() -> None:
    """The collisional declaration selects the gas-dynamic time."""
    classical = confinement_scalings(20.0, 1.0, 3.0e19, 1.0, 25.0, 2.0, False)
    assert classical.regime == REGIME_CLASSICAL
    assert classical.regime_time_s == classical.classical_time_s
    gas = confinement_scalings(20.0, 1.0, 3.0e19, 1.0, 25.0, 2.0, True)
    assert gas.regime == REGIME_GAS_DYNAMIC
    assert gas.regime_time_s == gas.gas_dynamic_time_s
    assert set(gas.to_record()) == {
        "log10_mirror_ratio",
        "classical_time_s",
        "sound_speed_m_s",
        "gas_dynamic_time_s",
        "gas_dynamic_printed_time_s",
        "regime",
        "regime_time_s",
    }


@pytest.mark.parametrize(
    "field",
    [
        "effective_ratio",
        "plasma_half_length_m",
        "density_per_m3",
        "electron_temperature_kev",
        "ion_energy_kev",
        "ion_mass_amu",
    ],
)
def test_non_positive_inputs_are_refused(field: str) -> None:
    """Every numeric input is strictly positive."""
    values: dict[str, Any] = {
        "effective_ratio": 10.0,
        "plasma_half_length_m": 1.0,
        "density_per_m3": 1.0e20,
        "electron_temperature_kev": 1.0,
        "ion_energy_kev": 1.0,
        "ion_mass_amu": 1.0,
        "collisional_regime": False,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        confinement_scalings(**values)
