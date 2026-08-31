# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — parameter model tests

"""Every validation branch of the magnetic-mirror parameter model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import (
    CellLayout,
    MirrorField,
    require_finite,
    require_positive,
)


def synthetic_field(**overrides: float) -> MirrorField:
    """Build a valid synthetic mirror field with optional overrides."""
    values: dict[str, float] = {"b_max_t": 10.0, "b_min_t": 1.0}
    values.update(overrides)
    return MirrorField(**values)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


def test_valid_field_and_derived_quantities() -> None:
    """A valid field derives the mirror ratio and loss-cone fraction."""
    field = synthetic_field()
    assert field.mirror_ratio == pytest.approx(10.0)
    assert field.loss_cone_fraction() == pytest.approx(1.0 - math.sqrt(0.9))


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"b_max_t": 0.0}, "b_max_t"),
        ({"b_min_t": -1.0}, "b_min_t"),
        ({"b_max_t": 1.0}, "strictly larger than"),
        ({"b_max_t": 0.5}, "strictly larger than"),
        ({"b_min_t": math.nan}, "b_min_t"),
    ],
)
def test_invalid_field_is_rejected(overrides: dict[str, float], fragment: str) -> None:
    """Each mirror-field violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_field(**overrides)


def test_valid_layouts() -> None:
    """Layouts with and without end plugs construct."""
    plain = CellLayout(central_cell_length_m=5.0, end_plug_cell_count=0)
    tandem = CellLayout(central_cell_length_m=5.0, end_plug_cell_count=2)
    assert plain.end_plug_cell_count == 0
    assert tandem.end_plug_cell_count == 2


def test_invalid_layouts_are_rejected() -> None:
    """Non-positive length and negative plug counts are rejected."""
    with pytest.raises(DeviceConfigurationError, match="central_cell_length_m"):
        CellLayout(central_cell_length_m=0.0, end_plug_cell_count=0)
    with pytest.raises(DeviceConfigurationError, match="end_plug_cell_count"):
        CellLayout(central_cell_length_m=5.0, end_plug_cell_count=-1)
