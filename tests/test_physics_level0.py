# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — level-0 record tests

"""Composition, identity, wiring, immutability pin and refusals of the record."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from typing import Any

import pytest

from physics_fixtures import configuration, inputs, tandem_inputs
from scpn_mirror_core import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    TandemInputs,
    level0_physics,
)
from scpn_mirror_core.errors import DeviceConfigurationError

REFERENCE_SIMPLE_SHA256 = (
    "f0fefd641810a462b4f53f32bd74f0c181a81a963fde2e79a17cf8b7a7699171"
)
REFERENCE_TANDEM_SHA256 = (
    "9fdabd0779083983791f044f0504c8f3c03a071eb6718a8d21bf682ea8c81635"
)


def test_record_composes_every_model_and_is_canonical() -> None:
    """The record carries the configuration digest and every model record."""
    config = configuration()
    record = level0_physics(config, inputs())
    assert isinstance(record, Level0PhysicsRecord)
    projected = record.to_record()
    assert projected["schema"] == LEVEL0_SCHEMA
    assert projected["schema_version"] == LEVEL0_SCHEMA_VERSION
    assert projected["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert projected["configuration_digest_sha256"] == config.digest_sha256()
    assert projected["plasma_half_length_m"] == 1.0
    assert projected["tandem"] is None
    assert set(projected) == {
        "schema",
        "schema_version",
        "non_claims",
        "configuration_digest_sha256",
        "inputs",
        "plasma_half_length_m",
        "mirror",
        "ion_loss_boundary",
        "electron_loss_boundary",
        "collisions",
        "confinement",
        "flr",
        "adiabaticity",
        "tandem",
    }
    data = record.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == projected
    assert record.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert level0_physics(config, inputs()).digest_sha256() == record.digest_sha256()


def test_reference_digests_are_pinned() -> None:
    """The simple and tandem reference records are immutability fixtures."""
    simple = level0_physics(configuration(), inputs())
    assert simple.digest_sha256() == REFERENCE_SIMPLE_SHA256
    tandem = level0_physics(
        configuration("tandem_mirror", central_cell_length_m=10.0),
        inputs(tandem=tandem_inputs()),
    )
    assert tandem.digest_sha256() == REFERENCE_TANDEM_SHA256


def test_models_are_wired_to_the_configuration_and_each_other() -> None:
    """Half length, midplane field, regime and electron loss follow the inputs."""
    record = level0_physics(configuration(), inputs())
    assert record.mirror.vacuum_ratio == 17.0 / 0.86
    assert record.confinement.regime == "classical"
    assert record.ion_loss_boundary.potential_factor == 1.0 + 5.0 / 25.0
    assert record.electron_loss_boundary.fully_confined
    assert record.flr.critical_mode_number > 0.0
    assert record.adiabaticity.alpha is not None
    gas = level0_physics(configuration("gas_dynamic_mirror", b_max_t=30.0), inputs())
    assert gas.confinement.regime == "gas_dynamic"
    assert gas.confinement.regime_time_s == gas.confinement.gas_dynamic_time_s


def test_tandem_record_carries_the_tandem_chain() -> None:
    """A tandem mirror evaluates the Pastukhov chain on the central cell."""
    record = level0_physics(
        configuration("tandem_mirror", central_cell_length_m=10.0),
        inputs(tandem=tandem_inputs()),
    )
    assert record.tandem is not None
    assert record.tandem.ion_scattering_time_s > 0.0
    assert (
        record.to_record()["tandem"]["combined_time_s"] == record.tandem.combined_time_s
    )
    assert record.to_record()["inputs"]["tandem"] == tandem_inputs().to_record()


def test_tandem_inputs_are_required_exactly_for_a_tandem() -> None:
    """Missing tandem inputs on a tandem, or present on another class, are refused."""
    with pytest.raises(DeviceConfigurationError, match="requires the tandem inputs"):
        level0_physics(configuration("tandem_mirror"), inputs())
    with pytest.raises(DeviceConfigurationError, match="carries no end plugs"):
        level0_physics(configuration(), inputs(tandem=tandem_inputs()))


def test_inputs_record_and_validation() -> None:
    """Every declared input is projected and validated."""
    model = inputs()
    record = model.to_record()
    assert record["tandem"] is None
    assert set(record) == {
        "midplane_beta",
        "ion_mass_amu",
        "ion_charge_number",
        "density_per_m3",
        "electron_temperature_kev",
        "ion_energy_kev",
        "plasma_radius_m",
        "potential_drop_kev",
        "parallel_velocity_fraction",
        "field_gradient_scale_length_m",
        "tandem",
    }
    for field in (
        "ion_mass_amu",
        "ion_charge_number",
        "density_per_m3",
        "electron_temperature_kev",
        "ion_energy_kev",
        "plasma_radius_m",
        "field_gradient_scale_length_m",
    ):
        overrides: dict[str, Any] = {field: 0.0}
        with pytest.raises(DeviceConfigurationError, match=field):
            dataclasses.replace(model, **overrides)
    with pytest.raises(DeviceConfigurationError, match="midplane_beta"):
        dataclasses.replace(model, midplane_beta=1.0)
    with pytest.raises(DeviceConfigurationError, match="potential_drop_kev"):
        dataclasses.replace(model, potential_drop_kev=-1.0)
    with pytest.raises(DeviceConfigurationError, match="potential_drop_kev"):
        dataclasses.replace(model, potential_drop_kev=math.nan)
    with pytest.raises(DeviceConfigurationError, match="parallel_velocity_fraction"):
        dataclasses.replace(model, parallel_velocity_fraction=1.5)
    assert isinstance(model, ModelInputs)


@pytest.mark.parametrize(
    "field",
    [
        "plug_density_per_m3",
        "central_ion_temperature_kev",
        "plug_electron_potential_kev",
    ],
)
def test_tandem_inputs_are_validated(field: str) -> None:
    """Every tandem input is strictly positive."""
    with pytest.raises(DeviceConfigurationError, match=field):
        tandem_inputs(**{field: 0.0})
    assert set(tandem_inputs().to_record()) == {
        "plug_density_per_m3",
        "central_ion_temperature_kev",
        "plug_electron_potential_kev",
    }
    assert isinstance(tandem_inputs(), TandemInputs)
