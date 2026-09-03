# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — device CAD model benchmark

"""Benchmark the tier-G2 device CAD model on the pinned B-rep back-end.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per operation, an unavailable back-end marked
explicitly, full provenance in the artefact. Four operations are timed on
the declared synthetic assembly: revolving the ten bodies and hashing the
manifest, the normalised STEP export, faceting all ten bodies, and the
full checked record build (which includes the tier-G1 reference
tessellation and the per-body evidence). There is one back-end: the
pinned third-party OpenCASCADE kernel through CadQuery. The composition
timed here is the model's own (``brep_bodies``), not a second copy of it.
Nothing measured here is a physics or engineering claim.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scpn_reactor_kernels.errors import CadUnavailableError  # noqa: E402

from scpn_mirror_core.configuration import (  # noqa: E402
    DeviceConfiguration,
    RegistryBinding,
)
from scpn_mirror_core.geometry import DeviceGeometry  # noqa: E402
from scpn_mirror_core.geometry.profile import FieldProfile  # noqa: E402
from scpn_mirror_core.parameters import CellLayout, MirrorField  # noqa: E402

SCHEMA: Final = "scpn-mirror-core.device-model-cad-benchmark.v1"
MIDPLANE_PLASMA_RADIUS_M: Final = 0.05
MIDPLANE_FIELD_T: Final = 0.5
THROAT_FIELD_T: Final = 8.0
REGISTRY_DIGEST: Final = (
    "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
)


def synthetic_design() -> tuple[DeviceConfiguration, DeviceGeometry, FieldProfile]:
    """Build the synthetic configuration, geometry and field profile.

    Returns
    -------
    (DeviceConfiguration, DeviceGeometry, FieldProfile)
        Synthetic values; nothing describes a real machine.
    """
    configuration = DeviceConfiguration(
        identifier="simple_magnetic_mirror",
        field=MirrorField(b_max_t=THROAT_FIELD_T, b_min_t=MIDPLANE_FIELD_T),
        layout=CellLayout(central_cell_length_m=2.4, end_plug_cell_count=0),
        collisional_regime=False,
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )
    geometry = DeviceGeometry(
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
    profile: FieldProfile = (
        (-2.0, 0.05),
        (-1.4, 4.0),
        (-1.2, THROAT_FIELD_T),
        (-0.6, 1.0),
        (0.0, MIDPLANE_FIELD_T),
        (0.6, 1.0),
        (1.2, THROAT_FIELD_T),
        (1.4, 4.0),
        (2.0, 0.05),
    )
    return configuration, geometry, profile


def operations() -> list[tuple[str, Callable[[], float]]]:
    """Build the timed operations on the declared device assembly.

    Returns
    -------
    list of (name, callable)
        Each callable performs one operation and returns a checksum.

    Raises
    ------
    CadUnavailableError
        If the CAD back-end is absent.
    """
    from scpn_reactor_kernels.cad import BrepAssembly, backend_versions, facet_assembly
    from scpn_reactor_kernels.cad import step_bytes as library_step_bytes

    from scpn_mirror_core.geometry import (
        axial_stations,
        brep_bodies,
        build_device_cad,
        build_device_model,
    )
    from scpn_mirror_core.geometry.cad import (
        CAD_MODEL_NON_CLAIMS,
        CAD_MODEL_SCHEMA,
        CAD_MODEL_SCHEMA_VERSION,
    )
    from scpn_mirror_core.geometry.model import MODEL_UNITS

    configuration, geometry, profile = synthetic_design()
    stations = axial_stations(configuration, geometry)
    tube_profile = build_device_model(
        configuration, geometry, MIDPLANE_PLASMA_RADIUS_M, profile, 8
    ).tube_profile

    def build() -> BrepAssembly:
        bodies, _ = brep_bodies(geometry, stations, tube_profile)
        return BrepAssembly(bodies)

    def build_timed() -> float:
        return float(len(build().manifest_sha256()))

    assembly = build()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }

    def export() -> float:
        return float(len(library_step_bytes(assembly, extras)))

    def facet() -> float:
        meshes = facet_assembly(assembly, 1.0e-4, 0.1)
        return sum(mesh.signed_volume_m3() for mesh in meshes)

    def record() -> float:
        model = build_device_cad(
            configuration, geometry, MIDPLANE_PLASMA_RADIUS_M, profile
        )
        return float(len(model.digest_sha256()))

    return [
        ("brep_build_and_manifest", build_timed),
        ("step_export_normalised", export),
        ("facet_ten_bodies", facet),
        ("device_cad_record_build", record),
    ]


def measure(run: Callable[[], float], warmup: int, repeats: int) -> dict[str, float]:
    """Time repeated operations and summarise them.

    Parameters
    ----------
    run
        Operation to time; returns a checksum so the work cannot be
        optimised away.
    warmup
        Discarded leading runs.
    repeats
        Timed runs.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min and max in milliseconds per operation.
    """
    for _ in range(warmup):
        run()
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        run()
        samples.append((time.perf_counter_ns() - start) / 1e6)
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    return {
        "p50_ms_per_operation": percentile(0.5),
        "p95_ms_per_operation": percentile(0.95),
        "p99_ms_per_operation": percentile(0.99),
        "mean_ms_per_operation": statistics.fmean(samples),
        "min_ms_per_operation": ordered[0],
        "max_ms_per_operation": ordered[-1],
    }


def provenance() -> dict[str, Any]:
    """Collect the environment provenance of a run.

    Returns
    -------
    dict[str, Any]
        Interpreter, platform, CPU model, commit and host-load context.
    """
    cpu_model = "unknown"
    with contextlib.suppress(OSError):
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    load = "unavailable"
    with contextlib.suppress(OSError):
        load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[0]
    commit = "unknown"
    git = shutil.which("git")
    if git is not None:
        with contextlib.suppress(OSError):
            commit = subprocess.run(  # noqa: S603
                [git, "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "load_average_1min_at_start": load,
        "commit": commit,
        "isolated_cores": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark command-line interface.

    Parameters
    ----------
    argv
        Argument vector; None reads sys.argv.

    Returns
    -------
    int
        0 on completion.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    results: list[dict[str, Any]] = []
    try:
        timed = operations()
    except CadUnavailableError as exc:
        results.append(
            {
                "name": "device_cad_model",
                "backend": "cadquery_ocp",
                "stats": None,
                "status": f"unavailable: {exc}",
            }
        )
    else:
        for name, run in timed:
            results.append(
                {
                    "name": name,
                    "backend": "cadquery_ocp",
                    "stats": measure(run, args.warmup, args.repeats),
                    "status": "measured",
                }
            )
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {"warmup": args.warmup, "repeats": args.repeats},
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"device_model_cad.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['name']}: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
