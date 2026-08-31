# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device configuration container

"""Device configuration container bound to the SPO reactor registry.

A :class:`DeviceConfiguration` composes a validated mirror field and
cell layout under exactly one of the three registry identifiers this
repository owns. The class invariants are hard: a tandem mirror carries
exactly two end plugs, the simple and gas-dynamic classes carry none
(R. F. Post, Nucl. Fusion 27 (1987) 1579), and only the gas-dynamic
class declares the collisional regime that defines it (V. V. Mirnov,
D. D. Ryutov, Sov. Tech. Phys. Lett. 5 (1979) 279). Serialisation is
canonical (sorted keys, no NaN or infinity accepted anywhere) and the
SHA-256 digest of those bytes identifies the exact parameter set. The
registry binding is a data pin only — this package never imports SCPN
Phase Orchestrator code.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Final

from scpn_mirror_core.errors import DeviceConfigurationError
from scpn_mirror_core.parameters import CellLayout, MirrorField

OWNED_CONFIGURATIONS: Final = (
    "gas_dynamic_mirror",
    "simple_magnetic_mirror",
    "tandem_mirror",
)
TANDEM_PLUG_COUNT: Final = 2
GAS_DYNAMIC_MIN_MIRROR_RATIO: Final = 10.0
LOSS_CONE_FRACTION_ADVISORY: Final = 0.5
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RegistryBinding:
    """Pin to one SPO reactor registry release.

    Parameters
    ----------
    version
        Registry release version; non-empty.
    digest_sha256
        Registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DeviceConfigurationError
        If either pin component is malformed.
    """

    version: str
    digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the registry pin.

        Raises
        ------
        DeviceConfigurationError
            If either pin component is malformed.
        """
        if not self.version:
            raise DeviceConfigurationError("registry.version: must be non-empty")
        if HEX_DIGEST.fullmatch(self.digest_sha256) is None:
            raise DeviceConfigurationError(
                "registry.digest_sha256: must be 64 lowercase hexadecimal "
                f"characters, got {self.digest_sha256!r}"
            )


@dataclass(frozen=True, slots=True)
class ConsistencyFinding:
    """One internal-consistency finding on a device configuration.

    Parameters
    ----------
    field
        Dotted field path the finding refers to.
    message
        Human-readable statement of the inconsistency.
    """

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class DeviceConfiguration:
    """Validated magnetic-mirror device configuration.

    Parameters
    ----------
    identifier
        SPO registry configuration identifier; one of
        ``gas_dynamic_mirror``, ``simple_magnetic_mirror``, or
        ``tandem_mirror``.
    field
        Validated axial mirror field.
    layout
        Validated cell layout.
    collisional_regime
        Whether the configuration operates in the collisional
        (gas-dynamic) confinement regime; required exactly for
        ``gas_dynamic_mirror``.
    registry
        Pin to the SPO reactor registry release the identifier belongs
        to.

    Raises
    ------
    DeviceConfigurationError
        If the identifier is not owned by this repository or a class
        invariant is violated.
    """

    identifier: str
    field: MirrorField
    layout: CellLayout
    collisional_regime: bool
    registry: RegistryBinding

    def __post_init__(self) -> None:
        """Validate identifier ownership and the class invariants.

        Raises
        ------
        DeviceConfigurationError
            If the identifier is not owned by this repository or a
            class invariant is violated.
        """
        if self.identifier not in OWNED_CONFIGURATIONS:
            raise DeviceConfigurationError(
                f"identifier: {self.identifier!r} is not owned by "
                f"SCPN-MIRROR-CORE; owned: {OWNED_CONFIGURATIONS!r}"
            )
        plugs = self.layout.end_plug_cell_count
        if self.identifier == "tandem_mirror" and plugs != TANDEM_PLUG_COUNT:
            raise DeviceConfigurationError(
                f"layout.end_plug_cell_count: tandem_mirror requires exactly "
                f"{TANDEM_PLUG_COUNT} end plugs, got {plugs!r}"
            )
        if self.identifier != "tandem_mirror" and plugs != 0:
            raise DeviceConfigurationError(
                f"layout.end_plug_cell_count: {self.identifier} requires "
                f"zero end plugs, got {plugs!r}"
            )
        if self.identifier == "gas_dynamic_mirror" and not self.collisional_regime:
            raise DeviceConfigurationError(
                "collisional_regime: gas_dynamic_mirror requires the "
                "collisional confinement regime that defines the class"
            )
        if self.identifier != "gas_dynamic_mirror" and self.collisional_regime:
            raise DeviceConfigurationError(
                f"collisional_regime: {self.identifier} is a collisionless mirror class"
            )

    def consistency_report(self) -> tuple[ConsistencyFinding, ...]:
        """Report physics-consistency findings without failing.

        Returns
        -------
        tuple of ConsistencyFinding
            Advisory findings from the documented estimates; empty when
            the declared field sits in the class regime. Findings are
            advisory instruments, not machine claims.
        """
        findings: list[ConsistencyFinding] = []
        fraction = self.field.loss_cone_fraction()
        if fraction > LOSS_CONE_FRACTION_ADVISORY:
            findings.append(
                ConsistencyFinding(
                    field="field.b_max_t",
                    message=(
                        f"loss-cone fraction {fraction:.3f} exceeds one half; "
                        "the majority of an isotropic distribution is born "
                        "in the loss cone"
                    ),
                )
            )
        ratio = self.field.mirror_ratio
        if (
            self.identifier == "gas_dynamic_mirror"
            and ratio < GAS_DYNAMIC_MIN_MIRROR_RATIO
        ):
            findings.append(
                ConsistencyFinding(
                    field="field.b_max_t",
                    message=(
                        f"mirror ratio {ratio:.2f} is below the gas-dynamic "
                        f"regime bound {GAS_DYNAMIC_MIN_MIRROR_RATIO:.0f}"
                    ),
                )
            )
        return tuple(findings)

    def to_record(self) -> dict[str, Any]:
        """Project the configuration to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Nested record with every declared parameter.
        """
        return {
            "identifier": self.identifier,
            "field": {
                "b_max_t": self.field.b_max_t,
                "b_min_t": self.field.b_min_t,
            },
            "layout": {
                "central_cell_length_m": self.layout.central_cell_length_m,
                "end_plug_cell_count": self.layout.end_plug_cell_count,
            },
            "collisional_regime": self.collisional_regime,
            "registry": {
                "version": self.registry.version,
                "digest_sha256": self.registry.digest_sha256,
            },
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the configuration canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact parameter set.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _require_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """Return one required mapping field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a mapping.

    Returns
    -------
    dict[str, Any]
        The nested mapping.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a mapping.
    """
    value = record.get(field)
    if not isinstance(value, dict):
        raise DeviceConfigurationError(f"{field}: must be an object")
    return value


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number.

    Returns
    -------
    float
        The numeric value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a real number.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceConfigurationError(f"{field}: must be a number, got {value!r}")
    return float(value)


def _integer(record: dict[str, Any], field: str) -> int:
    """Return one required integer field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold an integer.

    Returns
    -------
    int
        The integer value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not an integer.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeviceConfigurationError(f"{field}: must be an integer, got {value!r}")
    return value


def _boolean(record: dict[str, Any], field: str) -> bool:
    """Return one required boolean field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a boolean.

    Returns
    -------
    bool
        The boolean value.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a boolean.
    """
    value = record.get(field)
    if not isinstance(value, bool):
        raise DeviceConfigurationError(f"{field}: must be a boolean, got {value!r}")
    return value


def _string(record: dict[str, Any], field: str) -> str:
    """Return one required string field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a string.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DeviceConfigurationError(f"{field}: must be a string, got {value!r}")
    return value


def configuration_from_record(record: Any) -> DeviceConfiguration:
    """Build a validated configuration from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceConfiguration.to_record`.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the record shape or any value violates the model.
    """
    if not isinstance(record, dict):
        raise DeviceConfigurationError("record: must be an object")
    known = {"identifier", "field", "layout", "collisional_regime", "registry"}
    unknown = sorted(set(record) - known)
    if unknown:
        raise DeviceConfigurationError(f"record: unknown fields {unknown!r}")
    field = _require_mapping(record, "field")
    layout = _require_mapping(record, "layout")
    registry = _require_mapping(record, "registry")
    return DeviceConfiguration(
        identifier=_string(record, "identifier"),
        field=MirrorField(
            b_max_t=_number(field, "b_max_t"),
            b_min_t=_number(field, "b_min_t"),
        ),
        layout=CellLayout(
            central_cell_length_m=_number(layout, "central_cell_length_m"),
            end_plug_cell_count=_integer(layout, "end_plug_cell_count"),
        ),
        collisional_regime=_boolean(record, "collisional_regime"),
        registry=RegistryBinding(
            version=_string(registry, "version"),
            digest_sha256=_string(registry, "digest_sha256"),
        ),
    )


def configuration_from_bytes(data: bytes) -> DeviceConfiguration:
    """Build a validated configuration from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceConfigurationError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceConfigurationError(f"record: invalid JSON document: {exc}") from exc
    return configuration_from_record(record)
