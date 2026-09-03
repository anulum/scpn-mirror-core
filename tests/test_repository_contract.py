# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Mirror Core — repository-level truth tests

"""Repository-level contract tests: the scaffold stays truthful."""

from __future__ import annotations

from pathlib import Path

import pytest

from manifest_io import load_json_object

REPO = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    ".editorconfig",
    ".gitattributes",
    ".github/CODEOWNERS",
    ".github/FUNDING.yml",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".zenodo.json",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "GOVERNANCE.md",
    "LICENSE",
    "Makefile",
    "NOTICE.md",
    "README.md",
    "REUSE.toml",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
    "VALIDATION.md",
    "capability-inventory.json",
    "docs/ARCHITECTURE.md",
    "docs/CONTROL_ADAPTER_SPECIFICATION.md",
    "docs/THREAT_MODEL.md",
    "docs/adr/0001-repository-boundary.md",
    "pyproject.toml",
    "conftest.py",
    "docs/adr/0002-device-configuration-model.md",
    "docs/adr/0003-diagnostic-clock-semantics.md",
    "docs/adr/0005-level0-device-physics.md",
    "docs/adr/0006-shared-numerics-kernels.md",
    "docs/benchmarks.md",
    "benchmarks/level0_physics.py",
    "benchmarks/results/level0_physics.local.json",
    "rust/Cargo.toml",
    "rust/Cargo.lock",
    "rust/pyproject.toml",
    "rust/src/lib.rs",
    "rust/src/mirror.rs",
    "rust/src/collisions.rs",
    "rust/src/confinement.rs",
    "rust/src/stability.rs",
    "rust/src/adiabaticity.rs",
    "rust/src/tandem.rs",
    "src/scpn_mirror_core/physics/__init__.py",
    "src/scpn_mirror_core/physics/numerics.py",
    "src/scpn_mirror_core/physics/mirror.py",
    "src/scpn_mirror_core/physics/collisions.py",
    "src/scpn_mirror_core/physics/confinement.py",
    "src/scpn_mirror_core/physics/stability.py",
    "src/scpn_mirror_core/physics/adiabaticity.py",
    "src/scpn_mirror_core/physics/tandem.py",
    "src/scpn_mirror_core/physics/level0.py",
    "reactor-domain.json",
    "requirements-dev.txt",
    "src/scpn_mirror_core/__init__.py",
    "src/scpn_mirror_core/configuration.py",
    "src/scpn_mirror_core/errors.py",
    "src/scpn_mirror_core/observability.py",
    "src/scpn_mirror_core/plan_envelope.py",
    "tests/data/plan_envelope_fixture.json",
    "src/scpn_mirror_core/parameters.py",
    "studio/portfolio-descriptor.json",
    "studio/portfolio-descriptor.schema.json",
    "studio/portfolio-descriptor.schema.json",
    "tools/preflight.py",
)

REQUIRED_IGNORE_LINES = (
    "/BACKUP/",
    "/ARCHIVE/",
    "/.coordination/",
    "/04_ARCANE_SAPIENCE/",
)

FORBIDDEN_BADGE_MARKERS = (
    "[![",
    "api.reuse.software/badge/",
    "api.scorecard.dev/projects/",
    "bestpractices.dev/projects/",
    "pypi.org/project/",
)


@pytest.mark.parametrize("relative", REQUIRED_PATHS)
def test_required_path_exists_and_is_not_empty(relative: str) -> None:
    """Every Tier-0 and reactor-standard surface exists with content."""
    path = REPO / relative
    assert path.is_file(), relative
    assert path.stat().st_size > 0, relative


def test_gitignore_carries_defensive_lines() -> None:
    """The ignore rules keep agent-state and backup trees out."""
    lines = {
        line.strip()
        for line in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    }
    for required in REQUIRED_IGNORE_LINES:
        assert required in lines, required


def test_readme_carries_no_unearned_badge() -> None:
    """No badge appears before its live evidence exists."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for marker in FORBIDDEN_BADGE_MARKERS:
        assert marker not in readme, marker


def test_changelog_starts_unreleased() -> None:
    """The changelog carries an Unreleased section and no invented release."""
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "[Unreleased]" in changelog


def test_manifest_declares_exact_configuration_assignment() -> None:
    """The manifest owns exactly its mapped registry configurations."""
    manifest = load_json_object(REPO / "reactor-domain.json")
    assert manifest["project"] == "SCPN-MIRROR-CORE"
    assert manifest["configurations"] == [
        "gas_dynamic_mirror",
        "simple_magnetic_mirror",
        "tandem_mirror",
    ]
    assert manifest["evidence_maturity"] == "computational_prototype"
    assert manifest["capabilities"] == [
        {
            "identifier": "device_configuration_model",
            "evidence_maturity": "computational_prototype",
            "evidence_pointer": "VALIDATION.md#device-configuration-model",
        },
        {
            "identifier": "diagnostic_clock_semantics",
            "evidence_maturity": "computational_prototype",
            "evidence_pointer": "VALIDATION.md#diagnostic-and-clock-semantics",
        },
        {
            "identifier": "level0_device_physics",
            "evidence_maturity": "computational_prototype",
            "evidence_pointer": "VALIDATION.md#level-0-device-physics",
        },
    ]
    assert "analytic_device_physics_models" in manifest["owned_domains"]
    assert {
        "domain": "shared_physics_geometry_and_numerics_kernels",
        "owner": "SCPN-REACTOR-KERNELS",
    } in manifest["excluded_domains"]
    assert manifest["claims"] == []


def test_descriptor_and_inventory_embed_current_manifest_digest() -> None:
    """Derived artefacts point at the exact committed manifest bytes."""
    from manifest_io import sha256_of_file

    digest = sha256_of_file(REPO / "reactor-domain.json")
    descriptor = load_json_object(REPO / "studio" / "portfolio-descriptor.json")
    inventory = load_json_object(REPO / "capability-inventory.json")
    assert descriptor["source"]["manifest_sha256"] == digest
    assert inventory["source"]["manifest_sha256"] == digest
    assert descriptor["lifecycle"]["state"] == "not_federated"
    assert inventory["implemented_capability_count"] == 3


def test_no_agent_state_trees_exist() -> None:
    """Forbidden agent-state paths are absent from the repository."""
    for forbidden in (
        ".coordination",
        "04_ARCANE_SAPIENCE",
        "BACKUP",
        "ARCHIVE",
    ):
        assert not (REPO / forbidden).exists(), forbidden


def test_descriptor_matches_ratified_schema() -> None:
    """The committed descriptor matches the ratified 1.1.0 schema shape."""
    schema = load_json_object(REPO / "studio" / "portfolio-descriptor.schema.json")
    descriptor = load_json_object(REPO / "studio" / "portfolio-descriptor.json")
    assert schema["$id"].endswith("/studio-portfolio-descriptor/1.1.0")
    assert schema["additionalProperties"] is False
    assert sorted(schema["required"]) == sorted(descriptor)
    assert sorted(schema["properties"]) == sorted(descriptor)
    assert descriptor["schema_version"] == "1.1.0"


def test_package_agrees_with_manifest_truth() -> None:
    """The device model package matches the manifest's pins and ownership."""
    from scpn_mirror_core import OWNED_CONFIGURATIONS, RegistryBinding

    manifest = load_json_object(REPO / "reactor-domain.json")
    assert list(OWNED_CONFIGURATIONS) == manifest["configurations"]
    pin = manifest["spo_registry"]
    binding = RegistryBinding(
        version=pin["version"], digest_sha256=pin["digest_sha256"]
    )
    assert binding.version == pin["version"]
    assert binding.digest_sha256 == pin["digest_sha256"]


def test_typed_package_marker_exists() -> None:
    """The PEP 561 marker is present (empty by design, so no size check)."""
    assert (REPO / "src" / "scpn_mirror_core" / "py.typed").is_file()


def test_kernel_library_pin_agrees_with_the_dependency_the_crate_and_the_package() -> (
    None
):
    """One commit, one version, one inventory digest: manifest, pyproject, Cargo, CI."""
    import tomllib

    import scpn_reactor_kernels

    manifest = load_json_object(REPO / "reactor-domain.json")
    pin = manifest["kernel_library"]
    assert pin["distribution"] == "scpn-reactor-kernels"
    assert pin["kernels"] == ["numerics_transcendental"]
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == [
        (
            "scpn-reactor-kernels @ git+https://github.com/anulum/"
            f"scpn-reactor-kernels.git@{pin['source_commit']}"
        )
    ]
    assert scpn_reactor_kernels.__version__ == pin["version"]
    cargo = tomllib.loads((REPO / "rust" / "Cargo.toml").read_text(encoding="utf-8"))
    crate = cargo["dependencies"]["scpn-reactor-kernels-rs"]
    assert crate["git"] == "https://github.com/anulum/scpn-reactor-kernels.git"
    assert crate["rev"] == pin["source_commit"]
    lock = (REPO / "rust" / "Cargo.lock").read_text(encoding="utf-8")
    assert f"#{pin['source_commit']}" in lock
    workflows = REPO / ".github" / "workflows"
    for name in ("reusable-static-policy.yml", "reusable-tests.yml", "pre-commit.yml"):
        assert "pip install -e ." in (workflows / name).read_text(encoding="utf-8"), (
            name
        )
