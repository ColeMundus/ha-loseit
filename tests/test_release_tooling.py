"""Release tooling never infers versions or publishes from branch builds."""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.release_metadata import metadata

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release_tree(tmp_path):
    manifest = tmp_path / "custom_components/loseit/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"version": "1.2.3"}')
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.2.3"\n')
    return tmp_path


def test_current_stable_metadata_and_lock_agree():
    values = metadata(ROOT, "v0.1.0")
    assert values["version"] == "0.1.0"
    assert values["prerelease"] == "false"
    assert values["filename"] == "loseit-0.1.0.zip"
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    project = next(p for p in lock["package"] if p["name"] == "ha-loseit")
    assert project["version"] == values["version"]


def test_release_version_cross_check(release_tree):
    assert metadata(release_tree, "v1.2.3") == {
        "tag": "v1.2.3",
        "version": "1.2.3",
        "prerelease": "false",
        "filename": "loseit-1.2.3.zip",
    }


@pytest.mark.parametrize("version", ["1.2.3a1", "1.2.3b2", "1.2.3rc1"])
def test_prereleases_are_explicit(release_tree, version):
    (release_tree / "custom_components/loseit/manifest.json").write_text(
        json.dumps({"version": version})
    )
    (release_tree / "pyproject.toml").write_text(f'[project]\nversion="{version}"')
    assert metadata(release_tree, f"v{version}")["prerelease"] == "true"


@pytest.mark.parametrize("tag", ["1.2.3", "v1.2.4", "main", "v1.2.3\n", "v01.2.3"])
def test_malformed_or_mismatched_tags_rejected(release_tree, tag):
    with pytest.raises(ValueError, match="exactly matching"):
        metadata(release_tree, tag)


def test_project_manifest_mismatch_rejected(release_tree):
    (release_tree / "pyproject.toml").write_text('[project]\nversion="1.2.4"')
    with pytest.raises(ValueError, match="exactly matching"):
        metadata(release_tree, "v1.2.3")


@pytest.mark.parametrize("version", ["1.2", "01.2.3", "1.2.3-dev", "1.2.3+local"])
def test_unsupported_release_version_rejected(release_tree, version):
    (release_tree / "custom_components/loseit/manifest.json").write_text(
        json.dumps({"version": version})
    )
    (release_tree / "pyproject.toml").write_text(f'[project]\nversion="{version}"')
    with pytest.raises(ValueError, match="exactly matching"):
        metadata(release_tree, f"v{version}")


def test_metadata_cli_and_github_output(tmp_path):
    version = json.loads((ROOT / "custom_components/loseit/manifest.json").read_text())[
        "version"
    ]
    output = tmp_path / "github-output"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/release_metadata.py"),
            f"v{version}",
            "--github-output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    values = json.loads(result.stdout)
    assert (
        dict(line.split("=", 1) for line in output.read_text().splitlines()) == values
    )
