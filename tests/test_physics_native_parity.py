# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — native parity tests

"""Bit-exact parity between the Python floor and the native kernels.

The native module is an optional build (rust/, distribution
scpn-mirror-native) whose transcendental functions are the shared kernel
library's Rust crate at the pinned commit; these tests are skipped
hermetically when it is absent and compare float64 bit patterns, never
tolerances, when present. All parameter sets are synthetic fixtures.
"""

from __future__ import annotations

import pytest

from physics_fixtures import bits
from scpn_mirror_core.physics import (
    adiabaticity,
    collision_times,
    confinement_scalings,
    flr_criterion,
    loss_boundary,
    tandem_confinement,
)
from scpn_mirror_core.physics.mirror import MirrorRatio

native = pytest.importorskip("scpn_mirror_native")

GRID = [
    (ratio, beta, density, energy, mass)
    for ratio in (2.0, 19.767441860465116, 40.0)
    for beta in (0.0, 0.3, 0.9)
    for density in (3.0e19, 1.0e20)
    for energy in (1.0, 25.0)
    for mass in (1.0, 2.5)
]


def _bits(values: tuple[float, ...]) -> list[bytes]:
    return [bits(value) for value in values]


@pytest.mark.parametrize(("ratio", "beta", "density", "energy", "mass"), GRID)
def test_ratio_boundaries_collisions_and_confinement_are_bit_exact(
    ratio: float, beta: float, density: float, energy: float, mass: float
) -> None:
    """Every scalar of models 1-3 agrees bit for bit."""
    effective = ratio / (1.0 - beta) ** 0.5
    assert bits(native.effective_ratio(ratio, beta)) == bits(
        MirrorRatio(ratio, beta, effective).effective_ratio
    )
    for charge, drop in ((1.0, 5.0), (-1.0, 5.0), (1.0, 0.0), (-1.0, 0.0)):
        floor = loss_boundary(effective, charge, energy, drop)
        got = native.loss_boundary(effective, charge, energy, drop)
        assert _bits(got[:3]) == _bits(
            (floor.potential_factor, floor.sine_squared, floor.isotropic_fraction)
        )
        assert got[3] is floor.fully_confined
        assert got[4] is floor.no_trapped_region
    floor_c = collision_times(density, 1.0, energy, mass, 1.0)
    got_c = native.collision_times(density, 1.0, energy, mass, 1.0)
    assert _bits(got_c) == _bits(
        (
            floor_c.density_unit,
            floor_c.slowing_time_s,
            floor_c.ion_scattering_time_s,
            floor_c.electron_scattering_time_s,
            floor_c.equal_time_electron_temperature_kev,
        )
    )
    floor_s = confinement_scalings(effective, 1.0, density, 1.0, energy, mass, False)
    got_s = native.confinement_scalings(effective, 1.0, density, 1.0, energy, mass)
    assert _bits(got_s) == _bits(
        (
            floor_s.log10_mirror_ratio,
            floor_s.classical_time_s,
            floor_s.sound_speed_m_s,
            floor_s.gas_dynamic_time_s,
            floor_s.gas_dynamic_printed_time_s,
        )
    )


@pytest.mark.parametrize("fraction", [0.0, 0.25, 0.7071067811865476, 1.0])
@pytest.mark.parametrize("field", [0.32, 0.86, 3.0])
def test_flr_and_adiabaticity_are_bit_exact(fraction: float, field: float) -> None:
    """Gyromotion, critical mode number and alpha agree bit for bit."""
    floor_f = flr_criterion(0.1, 1.0, 25.0, 2.0, 1.0, field)
    got_f = native.flr_criterion(0.1, 1.0, 25.0, 2.0, 1.0, field)
    assert _bits(got_f[:4]) == _bits(
        (
            floor_f.ion_speed_m_s,
            floor_f.cyclotron_frequency_rad_s,
            floor_f.ion_gyroradius_m,
            floor_f.critical_mode_number,
        )
    )
    assert got_f[4] is floor_f.m2_stabilised
    floor_a = adiabaticity(0.5, fraction, 25.0, 2.0, 1.0, field)
    got_a = native.adiabaticity(0.5, fraction, 25.0, 2.0, 1.0, field)
    assert bits(got_a[0]) == bits(floor_a.parallel_speed_m_s)
    if fraction == 0.0:
        assert got_a[1:] == (None, None, None)
        assert (floor_a.parallel_gyroradius_m, floor_a.alpha, floor_a.adiabatic) == (
            None,
            None,
            None,
        )
    else:
        assert floor_a.parallel_gyroradius_m is not None
        assert floor_a.alpha is not None
        assert _bits(got_a[1:3]) == _bits(
            (floor_a.parallel_gyroradius_m, floor_a.alpha)
        )
        assert got_a[3] is floor_a.adiabatic


@pytest.mark.parametrize("ratio", [1.5, 20.0, 60.0])
@pytest.mark.parametrize("plug_density", [2.0e20, 5.0e20])
def test_tandem_chain_is_bit_exact(ratio: float, plug_density: float) -> None:
    """Every tandem quantity, including the optional hole energy, agrees."""
    args = (
        ratio,
        plug_density,
        1.0e20,
        5.0,
        10.0,
        2.5,
        1.0,
        0.86,
        10.0,
        0.2,
        30.0,
        0.7,
    )
    floor = tandem_confinement(*args)
    got = native.tandem_confinement(*args)
    assert _bits(got[:11]) == _bits(
        (
            floor.ion_confining_potential_kev,
            floor.potential_ratio,
            floor.pastukhov_function,
            floor.ion_scattering_time_s,
            floor.pastukhov_time_s,
            floor.ion_thermal_speed_m_s,
            floor.trapping_time_s,
            floor.ion_gyroradius_m,
            floor.radial_time_s,
            floor.combined_time_s,
            floor.hole_denominator,
        )
    )
    if floor.ambipolar_hole_energy_kev is None:
        assert got[11] is None
    else:
        assert got[11] is not None
        assert bits(got[11]) == bits(floor.ambipolar_hole_energy_kev)


def test_native_refusals_mirror_the_floor() -> None:
    """A library refusal inside the native chain is a ValueError."""
    with pytest.raises(ValueError, match="y"):
        native.tandem_confinement(
            20.0, 5.0e20, 1.0e20, 5.0, 1.0e-3, 2.5, 1.0, 0.86, 10.0, 0.2, 30.0, 0.7
        )
    with pytest.raises(ValueError, match="x"):
        native.confinement_scalings(0.0, 1.0, 1.0e20, 1.0, 1.0, 1.0)
