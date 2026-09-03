# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the magnetic bottle with its mirror throats, the
three owned linear classes with their hard cell invariants, and the
velocity-space loss cone the configuration model checks. The right-hand
text panel states only facts backed by the repository itself.

Outputs (written next to this script):

- ``repo_header.png`` — the magnetic bottle: throat coils, central
  cell, trapped bounce motion and loss-cone escape (used by
  ``README.md``).
- ``repo_header_cell_layouts.png`` — the three owned classes stacked
  with the end-plug invariant highlighted.
- ``repo_header_loss_cone.png`` — the velocity-space loss cone with
  the one-half fraction flag.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, no random input).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"
RED = "#ff3366"
GREEN = "#3ddc84"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configurations", "simple · tandem · gas_dynamic"),
    ("Plug Invariant", "tandem = 2 end plugs, others 0 (Post 1987)"),
    ("Collisional Regime", "gas-dynamic only (Mirnov-Ryutov 1979)"),
    ("Loss Cone", "fraction above one half flagged"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.74,
        "MIRROR CORE",
        color="white",
        fontsize=29,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.66,
        subtitle,
        color=CYAN,
        fontsize=11,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.615, 0.615], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.55
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def bottle_lines(
    ax: Any,
    x_start: float,
    x_end: float,
    z_max: float,
    pinch: float,
    y_centre: float = 0.0,
    lines: int = 9,
    colour: str = CYAN,
    lw: float = 1.0,
    alpha: float = 0.7,
) -> None:
    """Draw field lines of a magnetic bottle pinching at both ends."""
    xs = np.linspace(x_start, x_end, 400)
    mid = (x_start + x_end) / 2.0
    half = (x_end - x_start) / 2.0
    shape = pinch + (1.0 - pinch) * np.sqrt(
        np.clip(1.0 - ((xs - mid) / half) ** 2, 0.0, 1.0)
    )
    for frac in np.linspace(-1.0, 1.0, lines):
        if abs(frac) < 1e-9:
            ax.plot(
                [x_start, x_end],
                [y_centre, y_centre],
                color=colour,
                lw=0.6,
                alpha=alpha * 0.6,
            )
            continue
        ax.plot(
            xs,
            y_centre + frac * z_max * shape,
            color=colour,
            lw=lw,
            alpha=alpha,
        )


def generate_magnetic_bottle() -> None:
    """Generate ``repo_header.png``: the magnetic bottle."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-2.6, 2.6)

    grid_x = np.linspace(1.4, 8.6, 240)
    grid_z = np.linspace(-1.6, 1.6, 120)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    shape = 0.35 + (1 - 0.35) * np.sqrt(
        np.clip(1 - ((mesh_x - 5.0) / 3.6) ** 2, 0.0, 1.0)
    )
    rho = np.abs(mesh_z) / (1.15 * shape)
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 2.2) * (shape**0.6),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.85,
    )

    bottle_lines(ax, 1.4, 8.6, 1.5, 0.34, lines=11, lw=1.0, alpha=0.75)

    for coil_x in (1.4, 8.6):
        ax.add_patch(
            plt.Rectangle(
                (coil_x - 0.18, 0.62),
                0.36,
                0.5,
                fill=False,
                ec=MAGENTA,
                lw=1.8,
                alpha=0.9,
            )
        )
        ax.add_patch(
            plt.Rectangle(
                (coil_x - 0.18, -1.12),
                0.36,
                0.5,
                fill=False,
                ec=MAGENTA,
                lw=1.8,
                alpha=0.9,
            )
        )
    ax.text(
        1.4,
        1.42,
        "B_max",
        color=MAGENTA,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        8.6,
        1.42,
        "B_max",
        color=MAGENTA,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )
    ax.text(
        5.0,
        1.78,
        "B_min · central cell",
        color=PROBE,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.annotate(
        "",
        xy=(7.4, 0.0),
        xytext=(2.6, 0.0),
        arrowprops={"arrowstyle": "<->", "color": "white", "lw": 1.1, "alpha": 0.55},
    )
    ax.text(
        5.0,
        -0.4,
        "trapped bounce motion",
        color="white",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.6,
    )

    ax.annotate(
        "",
        xy=(9.05, 0.62),
        xytext=(8.55, 0.18),
        arrowprops={"arrowstyle": "->", "color": RED, "lw": 1.3, "alpha": 0.85},
    )
    ax.text(
        8.9,
        -0.55,
        "loss cone escape",
        color=RED,
        fontsize=7.5,
        fontfamily="monospace",
        ha="right",
        alpha=0.9,
    )

    ax.text(
        5.0,
        -2.3,
        "mirror ratio R = B_max / B_min · linear axisymmetric bottle",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "The Magnetic Bottle, Declared Truth")
    _save(fig, plt, "repo_header.png")


def generate_cell_layouts() -> None:
    """Generate ``repo_header_cell_layouts.png``: the three classes."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    rows = [
        ("simple_magnetic_mirror", 8.15, "two throats · zero plugs", CYAN),
        ("tandem_mirror", 5.0, "central cell + exactly two end plugs", MAGENTA),
        ("gas_dynamic_mirror", 1.85, "long collisional cell · R >> 1", PROBE),
    ]
    for name, row_y, note, colour in rows:
        ax.text(
            1.0,
            row_y + 1.25,
            name,
            color=colour,
            fontsize=9.5,
            fontfamily="monospace",
            alpha=0.95,
        )
        ax.text(
            8.9,
            row_y + 1.25,
            note,
            color="#667799",
            fontsize=7.5,
            fontfamily="monospace",
            ha="right",
            alpha=0.9,
        )
        bottle_lines(
            ax,
            1.2,
            8.9,
            0.78,
            0.36,
            y_centre=row_y,
            lines=7,
            colour=colour,
            lw=0.9,
            alpha=0.65,
        )
        if name == "tandem_mirror":
            for plug_x in (2.05, 8.05):
                ax.add_patch(
                    plt.Rectangle(
                        (plug_x - 0.35, row_y - 0.62),
                        0.7,
                        1.24,
                        fill=False,
                        ec=GREEN,
                        lw=1.5,
                        alpha=0.9,
                    )
                )
            ax.text(
                2.05,
                row_y - 0.95,
                "plug 1",
                color=GREEN,
                fontsize=7,
                fontfamily="monospace",
                ha="center",
                alpha=0.9,
            )
            ax.text(
                8.05,
                row_y - 0.95,
                "plug 2",
                color=GREEN,
                fontsize=7,
                fontfamily="monospace",
                ha="center",
                alpha=0.9,
            )
        if name == "gas_dynamic_mirror":
            grid_x = np.linspace(2.2, 8.2, 120)
            grid_z = np.linspace(-0.5, 0.5, 40)
            mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
            ax.contourf(
                mesh_x,
                mesh_z + row_y,
                np.exp(-np.abs(mesh_z) * 4.5) * np.exp(-(((mesh_x - 5.2) / 2.6) ** 2)),
                levels=16,
                cmap=_glow_cmap(),
                alpha=0.7,
            )

    ax.text(
        5.0,
        0.35,
        "coil class contradicting its identifier is rejected · Post, "
        "Nucl. Fusion 27 (1987) 1579",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Three Linear Classes, Hard Invariants")
    _save(fig, plt, "repo_header_cell_layouts.png")


def generate_loss_cone() -> None:
    """Generate ``repo_header_loss_cone.png``: velocity-space cone."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(-5, 5)
    ax.set_ylim(0, 6.4)

    ax.plot([-4.6, 4.6], [0.9, 0.9], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([0, 0], [0.9, 6.0], color=STEEL, lw=1.0, alpha=0.7)
    ax.text(
        4.55,
        0.55,
        r"$v_{\parallel}$",
        color="#8899bb",
        fontsize=10,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(
        0.15,
        5.8,
        r"$v_{\perp}$",
        color="#8899bb",
        fontsize=10,
        fontfamily="monospace",
    )

    grid_x = np.linspace(-4.4, 4.4, 220)
    grid_z = np.linspace(0.9, 5.8, 160)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    speed = np.sqrt(mesh_x**2 + (mesh_z - 0.9) ** 2)
    inside_cone = np.abs(mesh_x) > (mesh_z - 0.9) / np.tan(np.deg2rad(35))
    dist = np.exp(-(((speed - 2.6) / 1.15) ** 2))
    dist[inside_cone] *= 0.12
    ax.contourf(mesh_x, mesh_z, dist, levels=30, cmap=_glow_cmap(), alpha=0.85)

    for sign in (-1, 1):
        v_perp = np.linspace(0.9, 5.9, 100)
        ax.plot(
            sign * (v_perp - 0.9) / np.tan(np.deg2rad(35)),
            v_perp,
            color=RED,
            lw=1.6,
            alpha=0.9,
            ls=(0, (6, 3)),
        )
    ax.text(
        2.35,
        5.35,
        "loss cone",
        color=RED,
        fontsize=9,
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        2.35,
        5.02,
        "sin²θ_c = 1/R",
        color="#ff8899",
        fontsize=8,
        fontfamily="monospace",
        alpha=0.9,
    )

    for sign in (-0.9, 0.9):
        ax.annotate(
            "",
            xy=(sign * 2.4, 1.15),
            xytext=(sign * 0.7, 2.6),
            arrowprops={"arrowstyle": "->", "color": RED, "lw": 1.1, "alpha": 0.7},
        )
    ax.text(
        0,
        1.18,
        "escape",
        color=RED,
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.8,
    )

    ax.text(
        -3.3,
        4.4,
        "trapped",
        color=CYAN,
        fontsize=9,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.text(
        0,
        0.28,
        "declared mirror ratio sets the cone · fraction above one half flagged",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "The Loss Cone, Checked Not Assumed")
    _save(fig, plt, "repo_header_loss_cone.png")


if __name__ == "__main__":
    generate_magnetic_bottle()
    generate_cell_layouts()
    generate_loss_cone()
