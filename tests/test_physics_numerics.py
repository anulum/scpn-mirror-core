# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — numerics wrapper tests

"""The library kernels are the only transcendental path; refusals are re-raised."""

from __future__ import annotations

import pytest
from scpn_reactor_kernels import numerics as library

from scpn_mirror_core.errors import DeviceConfigurationError, NumericsError
from scpn_mirror_core.physics import exponential, natural_log, power


def test_wrappers_return_the_library_values_bit_for_bit() -> None:
    """Every wrapper is the library kernel."""
    assert natural_log(10.0) == library.natural_log(10.0)
    assert exponential(2.5) == library.exponential(2.5)
    assert power(40.0, 2.0 / 3.0) == library.power(40.0, 2.0 / 3.0)


@pytest.mark.parametrize(
    ("call", "fragment"),
    [
        (lambda: natural_log(0.0), "x"),
        (lambda: exponential(1.0e3), "y"),
        (lambda: power(-1.0, 0.5), "base"),
    ],
)
def test_refusals_are_re_raised_under_the_device_error(
    call: object, fragment: str
) -> None:
    """A library refusal becomes a NumericsError that is a configuration error."""
    assert callable(call)
    with pytest.raises(NumericsError, match=fragment) as info:
        call()
    assert isinstance(info.value, DeviceConfigurationError)
    assert info.value.__cause__ is not None
