# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — shared synthetic fixtures of the geometry tests

"""Configurations, geometries and field profiles shared by the geometry tests.

Two fixture sets, and the difference between them is the point.

The *reference* set is synthetic: round numbers chosen to exercise the
model, describing no machine.

The *anchor* set carries the dimensions printed in the WHAM physics basis
already on file (D. Endrizzi et al., J. Plasma Phys. 89 (2023) 975890501,
CC BY 4.0, sections 2 and 2.1): a target plasma of radius ``a = 0.1 m``;
``17 T``, ``5.5 cm`` warm bore HTS mirror magnets centred at
``z = +-98 cm``; two further coils near the midplane at ``z = +-20 cm``
that raise the central field to a maximum of ``0.86 T``. It exists so the
geometry tier can be checked against a published arrangement the way the
level-0 models are checked against published numbers.

Everything the source does not print is declared here and marked as
declared: the vessel bore and wall, the winding thicknesses and axial
lengths of both coil pairs, the expansion-tank bore, wall and length, and
the end-wall thickness. **The axial field profile between the printed
endpoints is declared too.** The source prints the field at the midplane
and at the magnets and no shape between them, so the intermediate samples
here are a declared monotone rise of the kind a solenoid of the declared
length produces; they describe no machine, and the model treats them as
what they are — a declared quantity it applies flux conservation to.
Reproducing a printed dimension is an anchor, never a claim about that
machine.
"""

from __future__ import annotations

import struct

from scpn_mirror_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_mirror_core.geometry import DeviceGeometry
from scpn_mirror_core.geometry.profile import FieldProfile
from scpn_mirror_core.parameters import CellLayout, MirrorField

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"

#: Declared plasma radius at the midplane of the synthetic design.
REFERENCE_MIDPLANE_PLASMA_RADIUS_M = 0.05
#: Synthetic axial field, in tesla, at the midplane and at a throat.
REFERENCE_MIDPLANE_FIELD_T = 0.5
REFERENCE_THROAT_FIELD_T = 8.0
#: Synthetic throat-to-throat separation.
REFERENCE_CELL_LENGTH_M = 2.4


def reference_configuration() -> DeviceConfiguration:
    """Return the synthetic axisymmetric mirror configuration of these tests."""
    return DeviceConfiguration(
        identifier="simple_magnetic_mirror",
        field=MirrorField(
            b_max_t=REFERENCE_THROAT_FIELD_T, b_min_t=REFERENCE_MIDPLANE_FIELD_T
        ),
        layout=CellLayout(
            central_cell_length_m=REFERENCE_CELL_LENGTH_M, end_plug_cell_count=0
        ),
        collisional_regime=False,
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def reference_geometry() -> DeviceGeometry:
    """Return the synthetic axisymmetric mirror envelope of these tests."""
    return DeviceGeometry(
        central_cell_vessel_bore_radius_m=0.2,
        central_cell_vessel_wall_thickness_m=0.01,
        central_cell_coil_offset_m=0.5,
        central_cell_coil_bore_radius_m=0.22,
        central_cell_coil_winding_thickness_m=0.06,
        central_cell_coil_length_m=0.3,
        mirror_coil_warm_bore_radius_m=0.06,
        mirror_coil_winding_thickness_m=0.08,
        mirror_coil_length_m=0.4,
        expander_tank_bore_radius_m=0.5,
        expander_tank_wall_thickness_m=0.01,
        expander_tank_length_m=1.0,
        end_wall_thickness_m=0.05,
    )


def reference_field_profile() -> FieldProfile:
    """Return the synthetic declared axial field profile of these tests.

    Nine samples: the midplane, a pair inside the central cell, the two
    throats at ``+-1.2 m`` where the field is largest, the outboard faces
    of the two mirror coils, and a pair well inside the expansion tanks
    where the field has fallen an order of magnitude below the midplane
    value and the flux tube has fanned out accordingly.
    """
    return (
        (-2.0, 0.05),
        (-1.4, 4.0),
        (-1.2, REFERENCE_THROAT_FIELD_T),
        (-0.6, 1.0),
        (0.0, REFERENCE_MIDPLANE_FIELD_T),
        (0.6, 1.0),
        (1.2, REFERENCE_THROAT_FIELD_T),
        (1.4, 4.0),
        (2.0, 0.05),
    )


#: Values printed in the WHAM physics basis, sections 2 and 2.1.
ANCHOR_MIDPLANE_PLASMA_RADIUS_M = 0.1
ANCHOR_WARM_BORE_RADIUS_M = 0.0275
ANCHOR_THROAT_POSITION_M = 0.98
ANCHOR_CENTRAL_CELL_COIL_OFFSET_M = 0.2
ANCHOR_MIDPLANE_FIELD_T = 0.86
ANCHOR_THROAT_FIELD_T = 17.0
#: Throat-to-throat separation implied by the printed magnet positions.
ANCHOR_CELL_LENGTH_M = 2.0 * ANCHOR_THROAT_POSITION_M


def anchor_configuration() -> DeviceConfiguration:
    """Return the configuration of the printed high-field mirror arrangement.

    The midplane and throat fields and the throat separation are the
    printed values. The device class is the collisionless mirror the
    source names for the arrangement it describes.
    """
    return DeviceConfiguration(
        identifier="simple_magnetic_mirror",
        field=MirrorField(
            b_max_t=ANCHOR_THROAT_FIELD_T, b_min_t=ANCHOR_MIDPLANE_FIELD_T
        ),
        layout=CellLayout(
            central_cell_length_m=ANCHOR_CELL_LENGTH_M, end_plug_cell_count=0
        ),
        collisional_regime=False,
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def anchor_geometry() -> DeviceGeometry:
    """Return the envelope of the printed high-field mirror arrangement.

    The mirror-coil warm bore and the central-cell coil offset are the
    printed values. The vessel bore and wall, both winding thicknesses,
    both coil axial lengths, the expansion-tank bore, wall and length and
    the end-wall thickness are declared because the source does not print
    them.
    """
    return DeviceGeometry(
        central_cell_vessel_bore_radius_m=0.15,
        central_cell_vessel_wall_thickness_m=0.01,
        central_cell_coil_offset_m=ANCHOR_CENTRAL_CELL_COIL_OFFSET_M,
        central_cell_coil_bore_radius_m=0.18,
        central_cell_coil_winding_thickness_m=0.05,
        central_cell_coil_length_m=0.1,
        mirror_coil_warm_bore_radius_m=ANCHOR_WARM_BORE_RADIUS_M,
        mirror_coil_winding_thickness_m=0.06,
        mirror_coil_length_m=0.05,
        expander_tank_bore_radius_m=0.6,
        expander_tank_wall_thickness_m=0.01,
        expander_tank_length_m=1.5,
        end_wall_thickness_m=0.03,
    )


def anchor_field_profile() -> FieldProfile:
    """Return the declared axial field profile of the anchor arrangement.

    The two endpoint values are printed: ``0.86 T`` at the midplane and
    ``17 T`` at the magnets centred at ``+-98 cm``. The four intermediate
    samples on each side are DECLARED — the source prints no axial
    profile — and describe a monotone rise of the kind a solenoid of the
    declared axial length produces. They describe no machine.
    """
    return (
        (-ANCHOR_THROAT_POSITION_M, ANCHOR_THROAT_FIELD_T),
        (-0.95, 12.0),
        (-0.9, 6.0),
        (-0.7, 1.6),
        (-0.4, 0.9),
        (0.0, ANCHOR_MIDPLANE_FIELD_T),
        (0.4, 0.9),
        (0.7, 1.6),
        (0.9, 6.0),
        (0.95, 12.0),
        (ANCHOR_THROAT_POSITION_M, ANCHOR_THROAT_FIELD_T),
    )


def coarse_anchor_field_profile() -> FieldProfile:
    """Return the anchor profile reduced to the printed endpoints alone.

    Three samples: the printed midplane field and the two printed throat
    fields, with nothing declared between them. It exists so a test can
    show what the linear-between-samples contract costs — the tube it
    implies is a different body from the one the finer profile implies,
    and the record has to be able to tell them apart.
    """
    return (
        (-ANCHOR_THROAT_POSITION_M, ANCHOR_THROAT_FIELD_T),
        (0.0, ANCHOR_MIDPLANE_FIELD_T),
        (ANCHOR_THROAT_POSITION_M, ANCHOR_THROAT_FIELD_T),
    )


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


def stream_bits(values: list[float]) -> bytes:
    """Return the concatenated bit patterns of a float stream."""
    return b"".join(bits(value) for value in values)
