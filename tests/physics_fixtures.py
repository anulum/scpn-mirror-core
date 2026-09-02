# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — shared fixtures of the level-0 physics tests

"""Synthetic configurations and inputs shared by the level-0 physics tests.

Every value is a test fixture; none describes a real machine. The
"WHAM-like" orders of magnitude (0.86 T midplane, 17 T throat, keV
temperatures) and the tandem case exist only so that statements printed
in the sources can serve as anchors.
"""

from __future__ import annotations

import struct
from typing import Any

from scpn_mirror_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_mirror_core.parameters import CellLayout, MirrorField
from scpn_mirror_core.physics import ModelInputs, TandemInputs

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
HALF_ROOT_TWO = 0.7071067811865476


def configuration(
    identifier: str = "simple_magnetic_mirror",
    b_max_t: float = 17.0,
    b_min_t: float = 0.86,
    central_cell_length_m: float = 2.0,
) -> DeviceConfiguration:
    """Return a synthetic configuration of the requested class."""
    plugs = 2 if identifier == "tandem_mirror" else 0
    return DeviceConfiguration(
        identifier=identifier,
        field=MirrorField(b_max_t=b_max_t, b_min_t=b_min_t),
        layout=CellLayout(
            central_cell_length_m=central_cell_length_m, end_plug_cell_count=plugs
        ),
        collisional_regime=identifier == "gas_dynamic_mirror",
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def tandem_inputs(**overrides: Any) -> TandemInputs:
    """Return synthetic tandem inputs with optional overrides."""
    values: dict[str, Any] = {
        "plug_density_per_m3": 5.0e20,
        "central_ion_temperature_kev": 10.0,
        "plug_electron_potential_kev": 30.0,
    }
    values.update(overrides)
    return TandemInputs(**values)


def inputs(**overrides: Any) -> ModelInputs:
    """Return synthetic model inputs with optional overrides."""
    values: dict[str, Any] = {
        "midplane_beta": 0.3,
        "ion_mass_amu": 2.0,
        "ion_charge_number": 1.0,
        "density_per_m3": 3.0e19,
        "electron_temperature_kev": 1.0,
        "ion_energy_kev": 25.0,
        "plasma_radius_m": 0.1,
        "potential_drop_kev": 5.0,
        "parallel_velocity_fraction": HALF_ROOT_TWO,
        "field_gradient_scale_length_m": 0.5,
        "tandem": None,
    }
    values.update(overrides)
    return ModelInputs(**values)


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)
