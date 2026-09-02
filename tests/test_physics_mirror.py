# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — mirror ratio and loss-boundary tests

"""Diamagnetic mirror ratio, loss boundaries and their refusals."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import configuration
from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.physics import loss_boundary, mirror_ratio, require_midplane_beta


def test_effective_ratio_follows_the_diamagnetic_form() -> None:
    """R_m = R_vac / sqrt(1 - beta) (Endrizzi eq. 3.6)."""
    config = configuration(b_max_t=10.0, b_min_t=1.0)
    ratio = mirror_ratio(config, 0.9)
    assert ratio.vacuum_ratio == 10.0
    assert ratio.midplane_beta == 0.9
    assert ratio.effective_ratio == 10.0 / math.sqrt(1.0 - 0.9)
    assert mirror_ratio(config, 0.0).effective_ratio == 10.0
    assert set(ratio.to_record()) == {
        "vacuum_ratio",
        "midplane_beta",
        "effective_ratio",
    }


@pytest.mark.parametrize("beta", [-0.1, 1.0, 1.5, math.nan, math.inf])
def test_beta_outside_the_half_open_interval_is_refused(beta: float) -> None:
    """The diamagnetic ratio needs 0 <= beta < 1."""
    with pytest.raises(DeviceConfigurationError, match="midplane_beta"):
        require_midplane_beta(beta)


def test_zero_potential_reduces_to_the_configuration_loss_cone() -> None:
    """At zero drop the isotropic fraction equals the configuration's, bit for bit."""
    config = configuration(b_max_t=10.0, b_min_t=1.0)
    boundary = loss_boundary(mirror_ratio(config, 0.0).effective_ratio, 1.0, 5.0, 0.0)
    assert boundary.potential_factor == 1.0
    assert boundary.sine_squared == 1.0 / 10.0
    assert boundary.isotropic_fraction == config.field.loss_cone_fraction()
    assert not boundary.fully_confined
    assert not boundary.no_trapped_region


def test_ions_see_a_wider_cone_and_electrons_a_narrower_one() -> None:
    """The potential factor is 1 + q Delta phi / E with the sign of q."""
    ions = loss_boundary(10.0, 1.0, 25.0, 5.0)
    electrons = loss_boundary(10.0, -1.0, 25.0, 5.0)
    assert ions.potential_factor == 1.2
    assert electrons.potential_factor == 0.8
    assert ions.sine_squared > 0.1 > electrons.sine_squared
    assert ions.isotropic_fraction == 1.0 - math.sqrt(1.0 - 0.12)


def test_electrons_below_the_drop_are_fully_confined() -> None:
    """An electron with E <= e Delta phi has no loss cone (source: only above 5 T_e)."""
    boundary = loss_boundary(10.0, -1.0, 5.0, 5.0)
    assert boundary.potential_factor == 0.0
    assert boundary.fully_confined
    assert boundary.sine_squared == 0.0
    assert boundary.isotropic_fraction == 0.0
    assert set(boundary.to_record()) == {
        "potential_factor",
        "sine_squared",
        "isotropic_fraction",
        "fully_confined",
        "no_trapped_region",
    }


def test_a_boundary_at_or_beyond_unity_means_no_trapped_region() -> None:
    """A wide cone that reaches sin^2 theta >= 1 is reported, not refused."""
    boundary = loss_boundary(1.5, 1.0, 1.0, 5.0)
    assert boundary.no_trapped_region
    assert boundary.sine_squared == 6.0 / 1.5
    assert boundary.isotropic_fraction == 1.0


@pytest.mark.parametrize(
    ("ratio", "energy", "drop", "field"),
    [
        (0.0, 1.0, 0.0, "effective_ratio"),
        (10.0, 0.0, 0.0, "energy_kev"),
        (10.0, 1.0, -1.0, "potential_drop_kev"),
        (10.0, 1.0, math.nan, "potential_drop_kev"),
    ],
)
def test_invalid_boundary_inputs_are_refused(
    ratio: float, energy: float, drop: float, field: str
) -> None:
    """Ratio and energy are strictly positive; the drop is finite and non-negative."""
    with pytest.raises(DeviceConfigurationError, match=field):
        loss_boundary(ratio, 1.0, energy, drop)
