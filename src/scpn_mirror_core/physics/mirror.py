# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — mirror ratio and loss boundary

"""Mirror ratio with plasma diamagnetism and the potential-modified loss boundary.

The vacuum mirror ratio ``R_vac = B_max / B_min`` of the validated
configuration is raised by the plasma's diamagnetic excavation of the
midplane field, ``R_m = R_vac (1 - beta)^(-1/2)`` (D. Endrizzi et al.,
J. Plasma Phys. 89 (2023) 975890501, eq. 3.6; S. Frank et al., J. Plasma
Phys. 91 (2025) E110, p. 2). A species of charge ``q`` and energy ``E``
that sees a potential drop ``Delta phi`` from the midplane to the throat
is lost when its midplane pitch satisfies
``sin^2 theta < (1 / R_m) (1 + q Delta phi / E)``: this is the loss
boundary of Frank et al. eqs. 2.3-2.5 written from the conservation of
the magnetic moment and the energy (the printed eq. 2.5b shows the
reciprocal fraction under the root, which at zero potential would exceed
one; the text states that at zero potential the boundary is the standard
loss cone, which this form gives). Ions (``q > 0``) see a wider cone,
electrons (``q < 0``) a narrower one, and an electron with ``E <= e Delta
phi`` is confined at every pitch. The fraction of an isotropic
distribution inside the cone, ``1 - sqrt(1 - sin^2 theta)``, reduces at
zero potential to the configuration's loss-cone fraction (Post 1987).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_mirror_core.configuration import DeviceConfiguration
from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import require_finite, require_positive


def require_midplane_beta(beta: float) -> float:
    """Return ``beta`` when it lies in ``[0, 1)``.

    Parameters
    ----------
    beta
        Midplane ``beta = 2 mu0 p / B_min^2``.

    Returns
    -------
    float
        The validated beta.

    Raises
    ------
    DeviceConfigurationError
        If ``beta`` is non-finite, negative or at least one; the
        diamagnetic mirror ratio carries a ``1 - beta`` root.
    """
    require_finite("midplane_beta", beta)
    if not 0.0 <= beta < 1.0:
        raise DeviceConfigurationError(
            "midplane_beta: the diamagnetic mirror ratio needs 0 <= beta < 1, "
            f"got {beta!r}"
        )
    return beta


@dataclass(frozen=True, slots=True)
class MirrorRatio:
    """Vacuum and diamagnetic mirror ratios of one configuration.

    Parameters
    ----------
    vacuum_ratio
        ``B_max / B_min``.
    midplane_beta
        Declared midplane beta.
    effective_ratio
        ``R_vac / sqrt(1 - beta)``.
    """

    vacuum_ratio: float
    midplane_beta: float
    effective_ratio: float

    def to_record(self) -> dict[str, Any]:
        """Project the ratios to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "vacuum_ratio": self.vacuum_ratio,
            "midplane_beta": self.midplane_beta,
            "effective_ratio": self.effective_ratio,
        }


@dataclass(frozen=True, slots=True)
class LossBoundary:
    """Loss boundary of one species at one energy.

    Parameters
    ----------
    potential_factor
        ``1 + q Delta phi / E``; non-positive means confined at every pitch.
    sine_squared
        ``sin^2 theta`` of the boundary (``0`` when fully confined; may
        reach or exceed one when no trapped region exists).
    isotropic_fraction
        Fraction of an isotropic distribution inside the cone.
    fully_confined
        ``True`` when the potential confines the species at every pitch.
    no_trapped_region
        ``True`` when the boundary reaches ``sin^2 theta >= 1``.
    """

    potential_factor: float
    sine_squared: float
    isotropic_fraction: float
    fully_confined: bool
    no_trapped_region: bool

    def to_record(self) -> dict[str, Any]:
        """Project the boundary to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "potential_factor": self.potential_factor,
            "sine_squared": self.sine_squared,
            "isotropic_fraction": self.isotropic_fraction,
            "fully_confined": self.fully_confined,
            "no_trapped_region": self.no_trapped_region,
        }


def mirror_ratio(
    configuration: DeviceConfiguration, midplane_beta: float
) -> MirrorRatio:
    """Evaluate the vacuum and diamagnetic mirror ratios.

    Parameters
    ----------
    configuration
        Validated mirror configuration.
    midplane_beta
        Declared midplane beta in ``[0, 1)``.

    Returns
    -------
    MirrorRatio
        Vacuum ratio, beta and the effective ratio of Endrizzi eq. 3.6.

    Raises
    ------
    DeviceConfigurationError
        If beta lies outside ``[0, 1)``.
    """
    beta = require_midplane_beta(midplane_beta)
    vacuum = configuration.field.mirror_ratio
    effective = vacuum / math.sqrt(1.0 - beta)
    return MirrorRatio(
        vacuum_ratio=vacuum, midplane_beta=beta, effective_ratio=effective
    )


def loss_boundary(
    effective_ratio: float,
    charge_number: float,
    energy_kev: float,
    potential_drop_kev: float,
) -> LossBoundary:
    """Evaluate the potential-modified loss boundary of one species.

    Parameters
    ----------
    effective_ratio
        Mirror ratio ``R_m``; strictly positive.
    charge_number
        Signed charge in units of ``e`` (``+Z`` for ions, ``-1`` for
        electrons).
    energy_kev
        Kinetic energy of the species at the midplane; strictly positive.
    potential_drop_kev
        ``Delta phi = phi_0 - phi_throat`` in kilovolts; non-negative.

    Returns
    -------
    LossBoundary
        The boundary and its disposition.

    Raises
    ------
    DeviceConfigurationError
        If the ratio or the energy is not strictly positive or the drop is
        negative.
    """
    require_positive("effective_ratio", effective_ratio)
    require_positive("energy_kev", energy_kev)
    require_finite("potential_drop_kev", potential_drop_kev)
    if potential_drop_kev < 0.0:
        raise DeviceConfigurationError(
            f"potential_drop_kev: must be non-negative, got {potential_drop_kev!r}"
        )
    factor = 1.0 + charge_number * potential_drop_kev / energy_kev
    if factor <= 0.0:
        return LossBoundary(
            potential_factor=factor,
            sine_squared=0.0,
            isotropic_fraction=0.0,
            fully_confined=True,
            no_trapped_region=False,
        )
    sine_squared = factor / effective_ratio
    if sine_squared >= 1.0:
        return LossBoundary(
            potential_factor=factor,
            sine_squared=sine_squared,
            isotropic_fraction=1.0,
            fully_confined=False,
            no_trapped_region=True,
        )
    return LossBoundary(
        potential_factor=factor,
        sine_squared=sine_squared,
        isotropic_fraction=1.0 - math.sqrt(1.0 - sine_squared),
        fully_confined=False,
        no_trapped_region=False,
    )
