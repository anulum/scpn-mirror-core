# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — declared field profile and flux-tube tests

"""The declared profile contract, flux conservation and aperture clearance.

The one physical relation this tier applies is
``r(z) = r_mid sqrt(B_mid / B(z))``, and it is checked here against an
independent evaluation of the same relation and against the mirror ratio
the configuration validates. The clearance bookkeeping is checked on
sections placed deliberately: one the tube never enters, one whose
boundary falls exactly on a sample, and one the tube fails. All values
are synthetic.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from geometry_fixtures import (
    REFERENCE_MIDPLANE_FIELD_T,
    REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
    REFERENCE_THROAT_FIELD_T,
    reference_configuration,
    reference_field_profile,
)
from scpn_mirror_core.errors import DeviceGeometryError
from scpn_mirror_core.geometry import (
    MIN_FIELD_SAMPLES,
    ApertureSection,
    flux_tube_clearances,
    flux_tube_profile,
    midplane_field_t,
    require_field_profile,
    throat_field_t,
)


def reference_tube() -> tuple[tuple[float, float], ...]:
    """Return the flux-tube profile of the synthetic reference design."""
    return flux_tube_profile(
        reference_field_profile(),
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M,
        REFERENCE_MIDPLANE_FIELD_T,
    )


def test_a_valid_profile_is_returned_unchanged() -> None:
    """Validation is a gate, not a transformation."""
    profile = reference_field_profile()
    assert require_field_profile("field_profile", profile) is profile


def test_a_profile_shorter_than_the_minimum_is_refused() -> None:
    """One sample cannot describe a field along an axis."""
    assert MIN_FIELD_SAMPLES == 2
    with pytest.raises(DeviceGeometryError, match="at least 2 samples"):
        require_field_profile("field_profile", ((0.0, 1.0),))
    with pytest.raises(DeviceGeometryError, match="at least 2 samples"):
        require_field_profile("field_profile", ())


def test_a_sample_that_is_not_a_pair_is_refused() -> None:
    """The rejection names the offending index.

    The malformed profile is typed as ``Any`` rather than suppressed: a
    caller who reaches this refusal did not have a well-typed value in the
    first place, and a type-checker suppression would hide that.
    """
    malformed: Any = ((0.0, 1.0), (1.0, 2.0, 3.0))
    with pytest.raises(DeviceGeometryError, match=r"field_profile\[1\]"):
        require_field_profile("field_profile", malformed)


@pytest.mark.parametrize("height", [math.nan, math.inf, -math.inf])
def test_a_non_finite_height_is_refused(height: float) -> None:
    """A sample at an undefined height fails closed."""
    with pytest.raises(DeviceGeometryError, match=r"field_profile\[1\].z"):
        require_field_profile("field_profile", ((0.0, 1.0), (height, 2.0)))


@pytest.mark.parametrize("strength", [0.0, -1.0, math.nan, math.inf])
def test_a_non_positive_or_non_finite_field_is_refused(strength: float) -> None:
    """A field of zero would put the flux tube at infinite radius."""
    with pytest.raises(DeviceGeometryError, match=r"field_profile\[1\].b_t"):
        require_field_profile("field_profile", ((0.0, 1.0), (1.0, strength)))


@pytest.mark.parametrize("height", [0.0, -0.5])
def test_heights_must_strictly_increase(height: float) -> None:
    """A repeated or decreasing height leaves the profile undefined."""
    with pytest.raises(DeviceGeometryError, match="must exceed the previous sample"):
        require_field_profile("field_profile", ((0.0, 1.0), (height, 2.0)))


def test_the_midplane_sample_is_the_reference_field() -> None:
    """The field the declared midplane radius belongs to is the z = 0 sample."""
    assert (
        midplane_field_t("field_profile", reference_field_profile())
        == REFERENCE_MIDPLANE_FIELD_T
    )


def test_a_profile_without_a_midplane_sample_is_refused() -> None:
    """The midplane radius is declared at the midplane, so z = 0 is required."""
    with pytest.raises(DeviceGeometryError, match=r"must carry a sample at z = 0\.0"):
        midplane_field_t("field_profile", ((-1.0, 5.0), (1.0, 5.0)))


def test_the_throat_field_is_the_largest_sample() -> None:
    """The throat field of a declared profile is its maximum."""
    assert throat_field_t(reference_field_profile()) == REFERENCE_THROAT_FIELD_T


def test_flux_conservation_is_applied_sample_by_sample() -> None:
    """Every radius is the declared relation evaluated independently."""
    profile = reference_field_profile()
    tube = reference_tube()
    assert len(tube) == len(profile)
    for (field_z, strength), (tube_z, radius) in zip(profile, tube, strict=True):
        assert tube_z == field_z
        expected = REFERENCE_MIDPLANE_PLASMA_RADIUS_M * math.sqrt(
            REFERENCE_MIDPLANE_FIELD_T / strength
        )
        assert radius == expected, field_z


def test_the_midplane_radius_is_reproduced_exactly() -> None:
    """At the reference field the relation is the identity, bit for bit."""
    midplane = next(radius for height, radius in reference_tube() if height == 0.0)
    assert midplane == REFERENCE_MIDPLANE_PLASMA_RADIUS_M


def test_the_throat_narrows_by_the_root_of_the_mirror_ratio() -> None:
    """The narrowest radius is the midplane radius over sqrt(R_m)."""
    ratio = reference_configuration().field.mirror_ratio
    narrowest = min(radius for _, radius in reference_tube())
    assert narrowest == pytest.approx(
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M / math.sqrt(ratio), rel=1.0e-15
    )
    assert narrowest * math.sqrt(ratio) == pytest.approx(
        REFERENCE_MIDPLANE_PLASMA_RADIUS_M, rel=1.0e-15
    )


def test_the_library_profile_contract_is_re_raised_under_the_device_error() -> None:
    """A radius the library refuses surfaces as a device geometry error."""
    with pytest.raises(DeviceGeometryError, match="flux_tube_profile"):
        flux_tube_profile(reference_field_profile(), 0.0, REFERENCE_MIDPLANE_FIELD_T)


def test_a_section_the_tube_never_enters_carries_no_clearance() -> None:
    """There is nothing to clear where the column does not go."""
    section = ApertureSection(
        name="beyond_the_column", z_low_m=10.0, z_high_m=11.0, bore_radius_m=0.001
    )
    assert flux_tube_clearances((section,), reference_tube()) == ()


def test_a_section_boundary_on_a_sample_reports_that_sample_exactly() -> None:
    """The interpolation returns the sample radius at the sample, not a rounding."""
    tube = reference_tube()
    midplane_radius = next(radius for height, radius in tube if height == 0.0)
    section = ApertureSection(
        name="midplane_slice", z_low_m=0.0, z_high_m=0.0, bore_radius_m=1.0
    )
    (clearance,) = flux_tube_clearances((section,), tube)
    assert clearance.largest_flux_tube_radius_m == midplane_radius
    assert clearance.clearance_m == 1.0 - midplane_radius
    assert clearance.section == "midplane_slice"


def test_the_largest_radius_inside_a_section_is_exact_between_samples() -> None:
    """A boundary between two samples reports the interpolated radius."""
    tube = reference_tube()
    low, high = tube[3], tube[4]
    middle = (low[0] + high[0]) / 2.0
    expected = low[1] + (middle - low[0]) * (high[1] - low[1]) / (high[0] - low[0])
    section = ApertureSection(
        name="half_band", z_low_m=low[0], z_high_m=middle, bore_radius_m=1.0
    )
    (clearance,) = flux_tube_clearances((section,), tube)
    assert clearance.largest_flux_tube_radius_m == expected


def test_a_tube_as_wide_as_the_bore_is_refused() -> None:
    """The clearance has to be strictly positive: touching is intersecting."""
    tube = reference_tube()
    midplane_radius = next(radius for height, radius in tube if height == 0.0)
    section = ApertureSection(
        name="central_cell_vessel",
        z_low_m=-0.1,
        z_high_m=0.1,
        bore_radius_m=midplane_radius,
    )
    with pytest.raises(DeviceGeometryError, match="central_cell_vessel"):
        flux_tube_clearances((section,), tube)


def test_the_refusal_names_the_section_and_its_bore() -> None:
    """A caller can find which aperture the column failed."""
    section = ApertureSection(
        name="mirror_coil_downstream", z_low_m=1.0, z_high_m=1.4, bore_radius_m=0.015
    )
    with pytest.raises(DeviceGeometryError) as raised:
        flux_tube_clearances((section,), reference_tube())
    message = str(raised.value)
    assert "mirror_coil_downstream" in message
    assert "0.015" in message
    assert "pass" in message


def test_clearances_project_to_json() -> None:
    """The clearance record carries the bore, the radius and the difference."""
    section = ApertureSection(
        name="central_cell_vessel", z_low_m=-1.0, z_high_m=1.0, bore_radius_m=0.2
    )
    (clearance,) = flux_tube_clearances((section,), reference_tube())
    record = clearance.to_record()
    assert record["section"] == "central_cell_vessel"
    assert record["bore_radius_m"] == 0.2
    assert record["clearance_m"] == (
        record["bore_radius_m"] - record["largest_flux_tube_radius_m"]
    )
