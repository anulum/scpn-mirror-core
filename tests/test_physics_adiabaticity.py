# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — adiabaticity parameter tests

"""Endrizzi section 3.6: alpha = L_B / rho_par, its threshold and refusals."""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.physics import (
    ADIABATICITY_THRESHOLD,
    adiabaticity,
    ion_gyromotion,
    require_fraction,
)


def test_alpha_is_the_gradient_length_over_the_parallel_gyroradius() -> None:
    """Alpha = L_B omega_ci / (f v)."""
    speed, frequency, _ = ion_gyromotion(25.0, 2.0, 1.0, 0.86)
    result = adiabaticity(0.5, 0.5, 25.0, 2.0, 1.0, 0.86)
    assert result.parallel_speed_m_s == 0.5 * speed
    assert result.parallel_gyroradius_m == 0.5 * speed / frequency
    assert result.alpha == 0.5 / (0.5 * speed / frequency)
    assert result.adiabatic is (result.alpha > ADIABATICITY_THRESHOLD)
    assert set(result.to_record()) == {
        "parallel_speed_m_s",
        "parallel_gyroradius_m",
        "alpha",
        "adiabatic",
    }


def test_alpha_scales_with_field_squared_and_inversely_with_the_fraction() -> None:
    """Doubling B doubles alpha (rho_par ∝ 1/B at fixed v); halving f doubles it."""
    base = adiabaticity(1.0, 0.5, 10.0, 2.0, 1.0, 1.0).alpha
    doubled_field = adiabaticity(1.0, 0.5, 10.0, 2.0, 1.0, 2.0).alpha
    halved_fraction = adiabaticity(1.0, 0.25, 10.0, 2.0, 1.0, 1.0).alpha
    assert (
        base is not None and doubled_field is not None and halved_fraction is not None
    )
    assert math.isclose(doubled_field / base, 2.0, rel_tol=1.0e-12)
    assert math.isclose(halved_fraction / base, 2.0, rel_tol=1.0e-12)


def test_threshold_dispositions() -> None:
    """A long gradient length is adiabatic; a short one is not."""
    assert adiabaticity(100.0, 0.5, 10.0, 2.0, 1.0, 1.0).adiabatic is True
    assert adiabaticity(1.0e-3, 0.5, 10.0, 2.0, 1.0, 1.0).adiabatic is False


def test_zero_fraction_is_not_applicable() -> None:
    """No parallel gyroradius exists for a purely perpendicular population."""
    result = adiabaticity(0.5, 0.0, 25.0, 2.0, 1.0, 0.86)
    assert result.parallel_speed_m_s == 0.0
    assert result.parallel_gyroradius_m is None
    assert result.alpha is None
    assert result.adiabatic is None


@pytest.mark.parametrize("value", [-0.1, 1.1, math.nan, math.inf])
def test_fractions_outside_the_unit_interval_are_refused(value: float) -> None:
    """The fraction lies in [0, 1]."""
    with pytest.raises(DeviceConfigurationError, match="fraction"):
        require_fraction("fraction", value)


@pytest.mark.parametrize(
    "field",
    [
        "field_gradient_scale_length_m",
        "ion_energy_kev",
        "ion_mass_amu",
        "charge_number",
        "field_t",
    ],
)
def test_non_positive_inputs_are_refused(field: str) -> None:
    """Every other input is strictly positive."""
    values: dict[str, Any] = {
        "field_gradient_scale_length_m": 0.5,
        "parallel_velocity_fraction": 0.5,
        "ion_energy_kev": 25.0,
        "ion_mass_amu": 2.0,
        "charge_number": 1.0,
        "field_t": 0.86,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        adiabaticity(**values)
