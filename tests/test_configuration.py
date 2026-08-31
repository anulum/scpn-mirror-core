# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device configuration container tests

"""Every branch of the device configuration container and its parsers.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from scpn_mirror_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import CellLayout, MirrorField

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)


def synthetic_configuration(
    identifier: str = "simple_magnetic_mirror",
    b_max_t: float = 10.0,
    end_plug_cell_count: int = 0,
    collisional_regime: bool = False,
) -> DeviceConfiguration:
    """Build a valid synthetic configuration with optional overrides."""
    return DeviceConfiguration(
        identifier=identifier,
        field=MirrorField(b_max_t=b_max_t, b_min_t=1.0),
        layout=CellLayout(
            central_cell_length_m=5.0,
            end_plug_cell_count=end_plug_cell_count,
        ),
        collisional_regime=collisional_regime,
        registry=REGISTRY,
    )


def test_registry_binding_rejects_bad_pins() -> None:
    """Malformed registry pins are rejected."""
    with pytest.raises(DeviceConfigurationError, match=r"registry\.version"):
        RegistryBinding(version="", digest_sha256="0" * 64)
    with pytest.raises(DeviceConfigurationError, match=r"registry\.digest_sha256"):
        RegistryBinding(version="1.0.0", digest_sha256="ZZ")


def test_all_owned_identifiers_construct() -> None:
    """Each owned identifier constructs with its class-consistent layout."""
    simple = synthetic_configuration()
    tandem = synthetic_configuration("tandem_mirror", end_plug_cell_count=2)
    gas = synthetic_configuration("gas_dynamic_mirror", collisional_regime=True)
    assert simple.identifier == "simple_magnetic_mirror"
    assert tandem.identifier == "tandem_mirror"
    assert gas.identifier == "gas_dynamic_mirror"


def test_unowned_identifier_is_rejected() -> None:
    """Identifiers outside this repository's ownership are rejected."""
    with pytest.raises(DeviceConfigurationError, match="not owned"):
        synthetic_configuration("cusp")


def test_plug_count_class_invariants() -> None:
    """Plug counts must match the configuration class exactly."""
    with pytest.raises(DeviceConfigurationError, match="exactly 2 end plugs"):
        synthetic_configuration("tandem_mirror", end_plug_cell_count=1)
    with pytest.raises(DeviceConfigurationError, match="zero end plugs"):
        synthetic_configuration(end_plug_cell_count=1)


def test_collisionality_class_invariants() -> None:
    """The collisional regime belongs exactly to the gas-dynamic class."""
    with pytest.raises(DeviceConfigurationError, match="requires the"):
        synthetic_configuration("gas_dynamic_mirror", collisional_regime=False)
    with pytest.raises(DeviceConfigurationError, match="collisionless"):
        synthetic_configuration(collisional_regime=True)


def test_consistency_report_clean_and_findings() -> None:
    """The report is empty in-regime and precise out of regime."""
    assert synthetic_configuration().consistency_report() == ()
    shallow = synthetic_configuration(b_max_t=1.25)
    findings = shallow.consistency_report()
    assert len(findings) == 1
    assert "loss cone" in findings[0].message
    weak_gdm = synthetic_configuration(
        "gas_dynamic_mirror", b_max_t=5.0, collisional_regime=True
    )
    findings = weak_gdm.consistency_report()
    assert len(findings) == 1
    assert "gas-dynamic" in findings[0].message


def test_canonical_round_trip_and_digest() -> None:
    """Canonical bytes round-trip losslessly and digest deterministically."""
    configuration = synthetic_configuration()
    data = configuration.canonical_bytes()
    assert data.endswith(b"\n")
    restored = configuration_from_bytes(data)
    assert restored == configuration
    expected = hashlib.sha256(data).hexdigest()
    assert configuration.digest_sha256() == expected


def test_from_record_round_trip_all_classes() -> None:
    """All owned configuration classes round-trip through records."""
    for configuration in (
        synthetic_configuration(),
        synthetic_configuration("tandem_mirror", end_plug_cell_count=2),
        synthetic_configuration("gas_dynamic_mirror", collisional_regime=True),
    ):
        assert configuration_from_record(configuration.to_record()) == configuration


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda _: "not-a-dict", "record: must be an object"),
        (lambda r: {**r, "extra": 1}, "unknown fields"),
        (lambda r: {**r, "field": None}, "field: must be an object"),
        (lambda r: {**r, "layout": []}, "layout: must be an object"),
        (lambda r: {**r, "registry": 7}, "registry: must be an object"),
        (lambda r: {**r, "identifier": 3}, "identifier: must be a string"),
        (
            lambda r: {**r, "collisional_regime": "no"},
            "collisional_regime: must be a boolean",
        ),
    ],
)
def test_from_record_shape_violations(mutate: Any, fragment: str) -> None:
    """Each record-shape violation is rejected with a precise message."""
    record = synthetic_configuration().to_record()
    with pytest.raises(DeviceConfigurationError, match=fragment):
        configuration_from_record(mutate(record))


def test_from_record_field_type_violations() -> None:
    """Nested field-type violations name the offending field."""
    record = synthetic_configuration().to_record()
    record["field"]["b_max_t"] = "big"
    with pytest.raises(DeviceConfigurationError, match="b_max_t: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["field"]["b_max_t"] = True
    with pytest.raises(DeviceConfigurationError, match="b_max_t: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["layout"]["end_plug_cell_count"] = 1.5
    with pytest.raises(DeviceConfigurationError, match="end_plug_cell_count: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["layout"]["end_plug_cell_count"] = True
    with pytest.raises(DeviceConfigurationError, match="end_plug_cell_count: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["registry"]["version"] = None
    with pytest.raises(DeviceConfigurationError, match="version: must be a string"):
        configuration_from_record(record)


def test_from_bytes_rejects_invalid_documents() -> None:
    """Invalid UTF-8, invalid JSON, and non-finite literals are rejected."""
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"\xff\xfe")
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"{not json")
    record = synthetic_configuration().to_record()
    text = json.dumps(record).replace("10.0", "NaN", 1)
    with pytest.raises(DeviceConfigurationError, match="non-finite JSON literal"):
        configuration_from_bytes(text.encode("utf-8"))


def test_integer_accepted_where_number_expected() -> None:
    """Integral JSON numbers are accepted for real-valued fields."""
    record = synthetic_configuration().to_record()
    record["field"]["b_max_t"] = 10
    restored = configuration_from_record(record)
    assert restored.field.b_max_t == 10.0
