# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — magnetic-mirror parameter model

"""Validated parameter objects of a magnetic-mirror configuration.

The derived quantity implements one standard result and nothing more:
the isotropic loss-cone fraction ``f_lc = 1 - sqrt(1 - 1/R_m)`` of a
mirror with ratio ``R_m = B_max / B_min`` (R. F. Post, Nucl. Fusion 27
(1987) 1579). It is a rough consistency instrument with documented
applicability bounds; no claim about any real machine follows from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_mirror_core.errors import DeviceConfigurationError


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class MirrorField:
    """Axial mirror-field parameters.

    Parameters
    ----------
    b_max_t
        Field at the mirror throat ``B_max`` in tesla; strictly positive
        and strictly larger than ``b_min_t``.
    b_min_t
        Field at the cell midplane ``B_min`` in tesla; strictly
        positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or the mirror ratio is not above
        one.
    """

    b_max_t: float
    b_min_t: float

    def __post_init__(self) -> None:
        """Validate the mirror-field invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or the mirror ratio is not
            above one.
        """
        require_positive("b_max_t", self.b_max_t)
        require_positive("b_min_t", self.b_min_t)
        if self.b_max_t <= self.b_min_t:
            raise DeviceConfigurationError(
                "b_max_t: must be strictly larger than b_min_t "
                f"({self.b_max_t!r} <= {self.b_min_t!r}) — a mirror ratio "
                "above one is the defining property of the family"
            )

    @property
    def mirror_ratio(self) -> float:
        """Mirror ratio ``R_m = B_max / B_min``.

        Returns
        -------
        float
            Ratio above one for a validated field.
        """
        return self.b_max_t / self.b_min_t

    def loss_cone_fraction(self) -> float:
        """Isotropic loss-cone fraction of the validated mirror.

        Returns
        -------
        float
            ``f_lc = 1 - sqrt(1 - 1/R_m)`` (Post, NF 27 (1987) 1579) —
            the fraction of an isotropic distribution born inside the
            loss cone; a consistency instrument, not a confinement
            claim.
        """
        return 1.0 - math.sqrt(1.0 - 1.0 / self.mirror_ratio)


@dataclass(frozen=True, slots=True)
class CellLayout:
    """Axial cell layout of a mirror configuration.

    Parameters
    ----------
    central_cell_length_m
        Central-cell length in metres; strictly positive.
    end_plug_cell_count
        Number of end-plug cells; zero or more.

    Raises
    ------
    DeviceConfigurationError
        If the length is non-positive or the plug count negative.
    """

    central_cell_length_m: float
    end_plug_cell_count: int

    def __post_init__(self) -> None:
        """Validate the cell-layout invariants.

        Raises
        ------
        DeviceConfigurationError
            If the length is non-positive or the plug count negative.
        """
        require_positive("central_cell_length_m", self.central_cell_length_m)
        if self.end_plug_cell_count < 0:
            raise DeviceConfigurationError(
                "end_plug_cell_count: must be non-negative, "
                f"got {self.end_plug_cell_count!r}"
            )
