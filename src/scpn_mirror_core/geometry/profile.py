# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — declared axial field profile and the flux tube it implies

"""The declared axial field profile and the one relation applied to it.

A magnetic mirror confines a **flux tube**, and a flux tube is not a body
of constant radius: conservation of magnetic flux through the column ties
its radius to the field strength along the axis,

    r(z) = r_mid sqrt(B_mid / B(z)),

so the column is widest where the field is weakest and narrowest at the
throats. That single relation is the whole physical content of this
module, and it is the only physics the geometry tier applies.

**The field profile is declared, never invented.** The caller supplies an
ordered sequence of ``(z, B)`` samples; this module validates them,
checks them against the validated configuration's own ``b_min_t`` and
``b_max_t``, and converts them into the ``(z, radius)`` profile the
shared library's surface-of-revolution kernels take
(:mod:`scpn_reactor_kernels.geometry.profiles`, ADR 0010). Nothing here
solves a field, fits a coil set or smooths a sample: between two samples
the library's contract is a straight line, and a caller who wants a finer
surface passes finer samples.

The aperture bookkeeping lives here for the same reason. A mirror is the
one family in the group whose plasma boundary must pass through an
aperture narrower than itself, so the model states, per section of the
machine, the largest flux-tube radius inside that section and the bore it
has to clear — and refuses a design where it does not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import Profile, require_profile

from scpn_mirror_core.errors import DeviceGeometryError

#: Fewest samples a declared axial field profile may carry.
MIN_FIELD_SAMPLES: Final = 2

#: Relative tolerance the declared profile has to meet the configuration's
#: own midplane and throat fields within. The fixtures pass the
#: configuration's values unchanged and meet it exactly; the tolerance
#: exists for a caller who computes the profile from a field model and
#: lands one rounding away.
FIELD_MATCH_RELATIVE_TOLERANCE: Final = 1.0e-12

#: One ``(z, B)`` sample of a declared axial field profile.
FieldSample = tuple[float, float]
#: An ordered, declared axial field profile.
FieldProfile = tuple[FieldSample, ...]


def require_field_profile(name: str, profile: FieldProfile) -> FieldProfile:
    """Return a declared axial field profile when it satisfies the contract.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    profile
        Candidate ``(z, B)`` samples.

    Returns
    -------
    FieldProfile
        The validated profile, unchanged.

    Raises
    ------
    DeviceGeometryError
        If the profile carries fewer than two samples, if a sample is not
        a pair, if any value is non-finite, if any field is not strictly
        positive, or if the heights do not strictly increase. The
        rejection names the sample index.
    """
    if len(profile) < MIN_FIELD_SAMPLES:
        raise DeviceGeometryError(
            f"{name}: must carry at least {MIN_FIELD_SAMPLES} samples, got "
            f"{len(profile)!r}"
        )
    previous_z: float | None = None
    for index, sample in enumerate(profile):
        if len(sample) != 2:
            raise DeviceGeometryError(
                f"{name}[{index}]: must be a (z, B) pair, got {sample!r}"
            )
        height, strength = sample
        if not math.isfinite(height):
            raise DeviceGeometryError(
                f"{name}[{index}].z: must be finite, got {height!r}"
            )
        if not math.isfinite(strength) or strength <= 0.0:
            raise DeviceGeometryError(
                f"{name}[{index}].b_t: must be finite and strictly positive, "
                f"got {strength!r}"
            )
        if previous_z is not None and not height > previous_z:
            raise DeviceGeometryError(
                f"{name}[{index}].z: must exceed the previous sample, got "
                f"{height!r} after {previous_z!r}"
            )
        previous_z = height
    return profile


def midplane_field_t(name: str, profile: FieldProfile) -> float:
    """Return the declared field at the midplane sample ``z = 0``.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    profile
        Validated declared field profile.

    Returns
    -------
    float
        The field of the sample at exactly ``z = 0``, which is the field
        the declared midplane plasma radius belongs to.

    Raises
    ------
    DeviceGeometryError
        If the profile carries no sample at ``z = 0``. The midplane
        radius is declared at the midplane, so the profile has to say
        what the field is there rather than leave it to interpolation.
    """
    for height, strength in profile:
        if height == 0.0:
            return strength
    raise DeviceGeometryError(
        f"{name}: must carry a sample at z = 0.0, the plane the declared "
        "midplane plasma radius belongs to, got heights "
        f"{[height for height, _ in profile]!r}"
    )


def throat_field_t(profile: FieldProfile) -> float:
    """Return the largest field of a validated declared profile.

    Parameters
    ----------
    profile
        Validated declared field profile.

    Returns
    -------
    float
        ``max B`` over the samples, which is the throat field of the
        declared profile.
    """
    return max(strength for _, strength in profile)


def flux_tube_profile(
    profile: FieldProfile,
    midplane_plasma_radius_m: float,
    reference_field_t: float,
) -> Profile:
    """Convert a declared field profile into the flux tube it implies.

    Parameters
    ----------
    profile
        Validated declared ``(z, B)`` samples.
    midplane_plasma_radius_m
        Declared plasma radius at the midplane, strictly positive.
    reference_field_t
        Field the midplane radius belongs to, strictly positive; the
        midplane sample of the same profile.

    Returns
    -------
    Profile
        ``(z, radius)`` samples with
        ``radius = midplane_plasma_radius_m * sqrt(reference_field_t / B)``
        at every declared height — the library's profile type, validated
        by the library's own contract.

    Raises
    ------
    DeviceGeometryError
        If the resulting profile violates the library's profile contract
        (the library's message is preserved).
    """
    samples = tuple(
        (height, midplane_plasma_radius_m * math.sqrt(reference_field_t / strength))
        for height, strength in profile
    )
    try:
        return require_profile("flux_tube_profile", samples)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class ApertureSection:
    """One axial section of the machine and the bore the plasma clears there.

    Parameters
    ----------
    name
        Body name whose bore the section belongs to.
    z_low_m, z_high_m
        Axial extent of the section; ``z_high_m`` exceeds ``z_low_m``.
    bore_radius_m
        Bore radius of that body, the aperture the flux tube has to fit
        inside anywhere within the section.
    """

    name: str
    z_low_m: float
    z_high_m: float
    bore_radius_m: float


@dataclass(frozen=True, slots=True)
class FluxTubeClearance:
    """The widest the flux tube gets inside one section, against its bore.

    Parameters
    ----------
    section
        Body name of the section.
    bore_radius_m
        Bore radius of that section.
    largest_flux_tube_radius_m
        Largest flux-tube radius anywhere inside the section, computed
        exactly: the profile is linear in radius between samples, so the
        largest value on a sub-interval is the larger of its two
        interpolated endpoints.
    clearance_m
        ``bore_radius_m - largest_flux_tube_radius_m``; strictly positive
        for a design the model accepts.
    """

    section: str
    bore_radius_m: float
    largest_flux_tube_radius_m: float
    clearance_m: float

    def to_record(self) -> dict[str, Any]:
        """Project the clearance to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Section name, its bore, the largest flux-tube radius inside
            it and the resulting clearance.
        """
        return {
            "section": self.section,
            "bore_radius_m": self.bore_radius_m,
            "largest_flux_tube_radius_m": self.largest_flux_tube_radius_m,
            "clearance_m": self.clearance_m,
        }


def _radius_at(
    height: float,
    low: tuple[float, float],
    high: tuple[float, float],
) -> float:
    """Return the flux-tube radius at a height inside one profile segment.

    The library's profile contract is linear in radius between samples,
    so this is that straight line and nothing else. The two sample
    heights are returned exactly rather than through the interpolation,
    which would round.

    Parameters
    ----------
    height
        Height inside ``[low[0], high[0]]``.
    low, high
        The two ``(z, radius)`` samples bounding the segment.

    Returns
    -------
    float
        The radius of the surface of revolution at that height.
    """
    low_z, low_radius = low
    high_z, high_radius = high
    if height == low_z:
        return low_radius
    if height == high_z:
        return high_radius
    return low_radius + (height - low_z) * (high_radius - low_radius) / (high_z - low_z)


def flux_tube_clearances(
    sections: tuple[ApertureSection, ...], profile: Profile
) -> tuple[FluxTubeClearance, ...]:
    """Check the flux tube against every bore it passes through.

    Parameters
    ----------
    sections
        Axial sections of the machine in ascending order of ``z``.
    profile
        Validated flux-tube ``(z, radius)`` profile.

    Returns
    -------
    tuple of FluxTubeClearance
        One entry per section the flux tube actually enters, in section
        order. A section the tube does not reach carries no entry and is
        absent from the record, because there is nothing to clear there.

    Raises
    ------
    DeviceGeometryError
        If the flux tube is as wide as, or wider than, the bore of a
        section it enters. The refusal names the section, its bore and
        the offending radius: a mirror whose column does not pass its own
        throat is not a design the model will draw.
    """
    clearances: list[FluxTubeClearance] = []
    for section in sections:
        largest: float | None = None
        for low, high in pairwise(profile):
            overlap_low = max(low[0], section.z_low_m)
            overlap_high = min(high[0], section.z_high_m)
            if overlap_high < overlap_low:
                continue
            candidate = max(
                _radius_at(overlap_low, low, high),
                _radius_at(overlap_high, low, high),
            )
            largest = candidate if largest is None else max(largest, candidate)
        if largest is None:
            continue
        if largest >= section.bore_radius_m:
            raise DeviceGeometryError(
                f"flux_tube_profile: must stay inside the bore of "
                f"{section.name} ({section.bore_radius_m!r} m) everywhere in "
                f"z = [{section.z_low_m!r}, {section.z_high_m!r}], got a "
                f"radius of {largest!r} m — the confined column has to pass "
                "through the aperture, not intersect it"
            )
        clearances.append(
            FluxTubeClearance(
                section=section.name,
                bore_radius_m=section.bore_radius_m,
                largest_flux_tube_radius_m=largest,
                clearance_m=section.bore_radius_m - largest,
            )
        )
    return tuple(clearances)
