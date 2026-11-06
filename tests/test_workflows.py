"""Regression contracts for CI/release trust boundaries and honest check naming."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    # BaseLoader preserves the GitHub 'on' key (YAML 1.2) rather than YAML 1.1 bools.
    return yaml.load(
        (ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader
    )


def test_ci_checks_are_independent_and_coverage_is_filesystem_scoped():
    ci = workflow("ci.yml")
    assert ci["name"] == "Validate"
    assert set(ci["jobs"]) == {"lint", "types", "tests", "package", "hassfest", "hacs"}
    assert ci["permissions"] == {"contents": "read"}
    assert "workflow_call" in ci["on"]
    steps = ci["jobs"]["tests"]["steps"]
    runs = "\n".join(step.get("run", "") for step in steps)
    # Module-only scope misses pure modules imported through the isolated test package.
    assert "--cov=custom_components/loseit --cov-branch" in runs
    assert "coverage.xml" in runs
    assert "--disable-socket" in (ROOT / "pyproject.toml").read_text()
    assert "fail_under = 90" in (ROOT / "pyproject.toml").read_text()
    assert ci["jobs"]["hacs"]["if"] == "github.event.repository.private == false"
    assert "local brands required" in ci["jobs"]["hacs"]["name"]
    assert "ignore" not in ci["jobs"]["hacs"]["steps"][-1]["with"]
    assert "tests/test_branding.py" in str(ci["jobs"]["package"])


def test_remote_action_wrappers_are_pinned_and_checkout_does_not_persist_credentials():
    # HACS's SHA-pinned wrapper still launches a mutable :main container image.
    for filename in ("ci.yml", "release.yml"):
        config = workflow(filename)
        for job in config["jobs"].values():
            for step in job.get("steps", []):
                if "uses" not in step:
                    continue
                action, sha = step["uses"].split("@")
                assert re.fullmatch(r"[0-9a-f]{40}", sha), step["uses"]
                if action == "actions/checkout":
                    assert step["with"]["persist-credentials"] == "false"


def test_publication_is_manual_opt_in_after_validation_and_build():
    release = workflow("release.yml")
    assert release["permissions"] == {"contents": "read"}
    assert release["on"]["workflow_dispatch"]["inputs"]["publish"]["default"] == "false"
    jobs = release["jobs"]
    assert jobs["validate"]["uses"] == "./.github/workflows/ci.yml"
    assert jobs["prepare"]["needs"] == "validate"
    assert jobs["publish"]["needs"] == "prepare"
    publish = jobs["publish"]
    assert publish["if"] == (
        "github.event_name == 'workflow_dispatch' && inputs.publish == true"
    )
    assert publish["permissions"] == {"contents": "write"}
    assert publish["environment"] == "release"
    runs = "\n".join(step.get("run", "") for step in publish["steps"])
    assert "--verify-tag" in runs
    assert "--latest=false" in runs
    assert "--prerelease" in runs
    assert "configuration_file_path=scripts/release-notes.yml" in runs
    assert "gh release view" in runs
    assert "gh release download" in runs
    assert "sha256sum --check SHA256SUMS" in runs
    assert "release create" not in str(jobs["prepare"])
    notes = yaml.safe_load((ROOT / "scripts/release-notes.yml").read_text())
    assert notes["changelog"]["categories"][-1]["labels"] == ["*"]


def test_remote_tag_checks_bracket_publication():
    steps = workflow("release.yml")["jobs"]["publish"]["steps"]
    guard = "python scripts/verify_release_tag.py"
    publish = next(step for step in steps if "gh release create" in step.get("run", ""))
    post = next(step for step in steps if "gh release view" in step.get("run", ""))
    assert steps.index(publish) < steps.index(post)
    assert publish["run"].count(guard) == post["run"].count(guard) == 1
    assert publish["run"].index(guard) < publish["run"].index("gh release create")
    assert post["run"].index(guard) < post["run"].index("gh release view")
    for step in (publish, post):
        assert step["env"]["EXPECTED_SHA"] == "${{ github.sha }}"
        assert step["env"]["GH_REPO"] == "${{ github.repository }}"
        assert step["env"]["GH_TOKEN"] == "${{ github.token }}"
        assert step["env"]["TAG"] == "${{ needs.prepare.outputs.tag }}"
        assert "${{" not in step["run"]


@pytest.mark.parametrize("moved", [False, True])
def test_remote_mismatch_aborts_before_create_and_after_publication(tmp_path, moved):
    """Execute the actual publication tail with real verifier and offline fake gh."""
    steps = workflow("release.yml")["jobs"]["publish"]["steps"]
    guard = "python scripts/verify_release_tag.py"
    publish = next(
        step["run"] for step in steps if "gh release create" in step.get("run", "")
    )
    post = next(
        step["run"] for step in steps if "gh release view" in step.get("run", "")
    )
    # The first shell command of the postpublication step is the same executable guard.
    assert post.splitlines()[0] == guard
    gh = tmp_path / "gh"
    gh.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "marker = pathlib.Path(os.environ['MARKER'])\n"
        "if sys.argv[1:3] == ['release', 'create']:\n"
        "    marker.write_text('created')\n"
        "else:\n"
        "    moved = os.environ['MOVED'] == 'true' or marker.exists()\n"
        "    sha = 'b' * 40 if moved else 'a' * 40\n"
        "    obj = {'type': 'commit', 'sha': sha}\n"
        "    print(json.dumps({'ref': 'refs/tags/v1.2.3', 'object': obj}))\n"
    )
    gh.chmod(0o755)
    marker = tmp_path / "created"
    env = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
        "GH_REPO": "example/integration",
        "GH_TOKEN": "synthetic-not-a-credential",
        "TAG": "v1.2.3",
        "EXPECTED_SHA": "a" * 40,
        "MOVED": str(moved).lower(),
        "MARKER": str(marker),
        "FILENAME": "synthetic.zip",
    }
    commands = "flags=()\n" + publish[publish.index(guard) :]
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", commands],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert (result.returncode != 0) == moved
    assert marker.exists() == (not moved)
    if not moved:
        # Simulate a tag moving after creation: the second guard must fail the job.
        result = subprocess.run(
            [sys.executable, "scripts/verify_release_tag.py"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 1
        assert "does not match" in result.stderr
    else:
        assert "does not match" in result.stderr


def test_dependency_updates_propose_reviewed_uv_and_action_changes():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    assert {update["package-ecosystem"] for update in config["updates"]} == {
        "uv",
        "github-actions",
    }
    assert all(
        update["schedule"]["interval"] == "weekly" for update in config["updates"]
    )
    assert "auto-merge" not in str(config)
