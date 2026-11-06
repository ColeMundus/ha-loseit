"""Validate an existing release tag against project and integration versions."""

import argparse
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:(a|b|rc)(?:0|[1-9]\d*))?"
)


def metadata(root: Path, tag: str) -> dict[str, str]:
    """Reject malformed tags, mismatched versions and unreviewed release syntax."""
    version = json.loads((root / "custom_components/loseit/manifest.json").read_text())[
        "version"
    ]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    match = VERSION.fullmatch(version)
    if not match or project != version or tag != f"v{version}":
        raise ValueError(
            "Tag must be v<version>, exactly matching manifest and pyproject"
        )
    return {
        "tag": tag,
        "version": version,
        "prerelease": str(bool(match.group(1))).lower(),
        "filename": f"loseit-{version}.zip",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    values = metadata(ROOT, args.tag)
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            output.writelines(f"{key}={value}\n" for key, value in values.items())
    print(json.dumps(values, sort_keys=True))


if __name__ == "__main__":
    main()
