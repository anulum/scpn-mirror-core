# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — FLR criterion tests

"""Endrizzi eq. 3.7 with the source's worked case and refusals."""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.physics import (
    ATOMIC_MASS_KG,
    ELEMENTARY_CHARGE_C,
    KEV_J,
    critical_mode_number,
    flr_criterion,
    ion_gyromotion,
)


def test_worked_case_of_the_source() -> None:
    """A / rho_i = 4, L_p / a = 10 give m_crit = 0.8: all m >= 2 stabilised."""
    assert math.isclose(critical_mode_number(0.1, 1.0, 0.025), 0.8, rel_tol=1.0e-15)


def test_gyromotion_follows_the_declared_definitions() -> None:
    """V = sqrt(2 E / m), omega = Z e B / m, rho = v / omega."""
    speed, frequency, gyroradius = ion_gyromotion(10.0, 2.0, 1.0, 0.5)
    mass = 2.0 * ATOMIC_MASS_KG
    assert speed == math.sqrt(2.0 * 10.0 * KEV_J / mass)
    assert frequency == ELEMENTARY_CHARGE_C * 0.5 / mass
    assert gyroradius == speed / frequency


def test_criterion_disposition_switches_at_two() -> None:
    """Short plasmas fail the m = 2 condition; long ones satisfy it."""
    long = flr_criterion(0.1, 10.0, 25.0, 2.0, 1.0, 0.86)
    assert long.m2_stabilised
    assert long.critical_mode_number == critical_mode_number(
        0.1, 10.0, long.ion_gyroradius_m
    )
    short = flr_criterion(0.1, 0.05, 25.0, 2.0, 1.0, 0.86)
    assert not short.m2_stabilised
    assert set(short.to_record()) == {
        "ion_speed_m_s",
        "cyclotron_frequency_rad_s",
        "ion_gyroradius_m",
        "critical_mode_number",
        "m2_stabilised",
    }


@pytest.mark.parametrize(
    "field",
    [
        "plasma_radius_m",
        "plasma_half_length_m",
        "ion_energy_kev",
        "ion_mass_amu",
        "charge_number",
        "field_t",
    ],
)
def test_non_positive_inputs_are_refused(field: str) -> None:
    """Every input is strictly positive."""
    values: dict[str, Any] = {
        "plasma_radius_m": 0.1,
        "plasma_half_length_m": 1.0,
        "ion_energy_kev": 25.0,
        "ion_mass_amu": 2.0,
        "charge_number": 1.0,
        "field_t": 0.86,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        flr_criterion(**values)


def test_critical_mode_number_refuses_a_zero_gyroradius() -> None:
    """The gyroradius denominator is strictly positive."""
    with pytest.raises(DeviceConfigurationError, match="ion_gyroradius_m"):
        critical_mode_number(0.1, 1.0, 0.0)
