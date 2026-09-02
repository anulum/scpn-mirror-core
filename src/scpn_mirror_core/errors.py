# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device capability model errors

"""Error surface of the device capability models."""

from __future__ import annotations


class DeviceConfigurationError(ValueError):
    """Raised when a device configuration value violates a model invariant.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected.
    """


class DiagnosticPlanError(ValueError):
    """Raised when a diagnostic or clock declaration violates the model.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected.
    """


class NumericsError(DeviceConfigurationError):
    """Raised when a level-0 evaluation leaves the domain of a numerics kernel.

    The shared kernel library refuses (never clamps) a logarithm of a
    non-positive or subnormal argument and an exponential outside its
    normal-result window; this error re-raises that refusal under the
    device error type with the library's message.
    """
