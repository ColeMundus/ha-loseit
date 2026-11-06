"""Fail closed unless the remote release tag resolves to EXPECTED_SHA via gh API.

Inputs are GH_REPO, TAG and EXPECTED_SHA; gh authenticates using GH_TOKEN.
Only GET requests are made. No release or git ref is created or modified.
"""

import json
import os
import re
import subprocess
import sys
from urllib.parse import quote

MAX_TAG_DEPTH = 8
SHA = re.compile(r"[0-9a-f]{40}")
REPOSITORY = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*")


def valid_sha(value: object) -> bool:
    """Accept only full GitHub Git object IDs, never abbreviated SHAs or refs."""
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def lookup(endpoint: str) -> dict[str, object]:
    """Use authenticated gh GET with argv (not a shell); suppress raw error data."""
    try:
        result = subprocess.run(
            ["gh", "api", "--method", "GET", "--hostname", "github.com", endpoint],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        value = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        raise ValueError("Remote tag lookup failed") from None
    if not isinstance(value, dict):
        raise ValueError("Malformed remote tag response")
    return value


def target(response: dict[str, object]) -> tuple[str, str]:
    """Validate the target type and SHA before using them in another request."""
    obj = response.get("object")
    if not isinstance(obj, dict):
        raise ValueError("Missing remote tag target")
    kind, sha = obj.get("type"), obj.get("sha")
    if kind not in ("commit", "tag") or not valid_sha(sha):
        raise ValueError("Invalid remote tag target type or SHA")
    assert isinstance(kind, str) and isinstance(sha, str)
    return kind, sha


def verify_release_tag(repository: str, tag: str, expected_sha: str) -> str:
    """Peel at most eight annotated tags and require the workflow's exact commit."""
    if not valid_sha(expected_sha):
        raise ValueError("Invalid expected commit SHA")
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("Invalid GitHub repository")
    if not tag or any(ord(char) < 32 or ord(char) == 127 for char in tag):
        raise ValueError("Invalid release tag")
    prefix = f"repos/{repository}/git"
    response = lookup(f"{prefix}/ref/tags/{quote(tag, safe='')}")
    if response.get("ref") != f"refs/tags/{tag}":
        raise ValueError("Remote tag ref does not match requested tag")
    kind, sha = target(response)
    visited: set[str] = set()
    while kind == "tag":
        if sha in visited:
            raise ValueError("Remote annotated tag cycle")
        if len(visited) >= MAX_TAG_DEPTH:
            raise ValueError("Remote annotated tag depth exceeded")
        visited.add(sha)
        response = lookup(f"{prefix}/tags/{sha}")
        if response.get("sha") != sha:
            raise ValueError("Remote annotated tag SHA does not match request")
        kind, sha = target(response)
    if sha != expected_sha:
        raise ValueError("Remote tag commit does not match expected workflow commit")
    return sha


def main() -> None:
    try:
        commit = verify_release_tag(
            os.environ["GH_REPO"], os.environ["TAG"], os.environ["EXPECTED_SHA"]
        )
    except (KeyError, ValueError) as error:
        message = (
            "Missing release verification environment"
            if isinstance(error, KeyError)
            else str(error)
        )
        print(message, file=sys.stderr)
        raise SystemExit(1) from None
    print(f"Remote release tag verified at commit {commit}")


if __name__ == "__main__":
    main()
