"""Manual installation distribution is deterministic, complete and fail-closed."""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import pytest

from scripts import package

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_tree(tmp_path):
    root = tmp_path / "source"
    for name in (*package.RUNTIME_FILES, *package.BRAND_FILES):
        target = root / package.PREFIX / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / package.PREFIX / name, target)
    for name in package.NOTICES:
        shutil.copyfile(ROOT / name, root / name)
    return root


def test_installation_archive_is_allowlisted_and_self_contained(tmp_path):
    output = tmp_path / "loseit.zip"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/package.py"), str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    with ZipFile(output) as archive:
        names = archive.namelist()
        assert set(names) == {
            package.PREFIX + name
            for name in (*package.RUNTIME_FILES, *package.BRAND_FILES, *package.NOTICES)
        }
        assert archive.testzip() is None
        for name in names:
            assert ".." not in Path(name).parts
            assert b"loseit-private" not in archive.read(name)
            assert archive.getinfo(name).external_attr >> 16 == 0o100644
        for name in (*package.NOTICES, *package.BRAND_FILES):
            assert (
                archive.read(package.PREFIX + name)
                == (
                    ROOT / package.PREFIX / name
                    if name in package.BRAND_FILES
                    else ROOT / name
                ).read_bytes()
            )
        assert package.PREFIX + "brand/icon.svg" not in names
        notice = archive.read(package.PREFIX + "brand/NOTICE.md").decode()
        assert "FitNow, Inc." in notice
        assert "**not** this artwork" in notice
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    assert (tmp_path / "SHA256SUMS").read_text() == f"{checksum}  loseit.zip\n"
    # Native HACS downloads repository source, not this generic manual ZIP layout.
    import json

    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert not hacs.get("zip_release")
    assert not hacs.get("content_in_root")
    assert "filename" not in hacs


def test_extracted_archive_imports_without_repository_files(tmp_path):
    """The installation must not accidentally depend on root tools or test loaders."""
    output = tmp_path / "loseit.zip"
    package.build(ROOT, output)
    installation = tmp_path / "configuration"
    installation.mkdir()
    with ZipFile(output) as archive:
        archive.extractall(installation)
    assert not (installation / "pyproject.toml").exists()
    code = """
import importlib
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
for name in (
    "client", "config_flow", "const", "coordinator", "diagnostics",
    "request_gate", "sensor", "gwt", "models", "protocol", "schemas", "snapshot",
):
    module = importlib.import_module(f"custom_components.loseit.{name}")
    assert Path(module.__file__).resolve().is_relative_to(root)
from custom_components.loseit.client import DailySnapshot
from custom_components.loseit.models import DailySnapshot as Model
assert DailySnapshot is Model
print("Extracted integration imports successfully")
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(installation)],
        cwd=installation,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert "Extracted integration imports successfully" in result.stdout


def test_package_is_reproducible_and_ignores_nonruntime_data(source_tree, tmp_path):
    private = source_tree / package.PREFIX / "private"
    private.mkdir()
    (private / "cookies.json").write_text("synthetic secret")
    (source_tree / package.PREFIX / "capture.txt").write_text("synthetic secret")
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    package.build(source_tree, first)
    for path in source_tree.rglob("*"):
        if path.is_file():
            path.touch()
    package.build(source_tree, second)
    assert first.read_bytes() == second.read_bytes()
    package.verify(first, package.sources(source_tree))


@pytest.mark.parametrize("name", package.NOTICES)
@pytest.mark.parametrize("condition", ["missing", "empty", "symlink"])
def test_distribution_requires_real_nonempty_notices(source_tree, name, condition):
    path = source_tree / name
    path.unlink()
    if condition == "empty":
        path.write_text(" ")
    elif condition == "symlink":
        path.symlink_to(ROOT / name)
    with pytest.raises(ValueError, match="distribution notice"):
        package.sources(source_tree)


@pytest.mark.parametrize(
    "name", ["client.py", "translations/en.json", "brand/icon.png"]
)
def test_linked_runtime_files_are_rejected(source_tree, name):
    path = source_tree / package.PREFIX / name
    path.unlink()
    path.symlink_to(ROOT / package.PREFIX / name)
    with pytest.raises(ValueError, match="linked runtime|symlink"):
        package.sources(source_tree)


@pytest.mark.parametrize(
    "directory",
    [
        "custom_components",
        package.PREFIX,
        package.PREFIX + "translations",
        package.PREFIX + "brand",
    ],
)
def test_linked_runtime_directories_are_rejected(source_tree, tmp_path, directory):
    path = source_tree / directory
    target = tmp_path / "linked"
    path.rename(target)
    path.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        package.sources(source_tree)


@pytest.mark.parametrize("name", ["debug.py", "cookies.json", "translations/new.json"])
def test_new_runtime_files_require_allowlist_review(source_tree, name):
    (source_tree / package.PREFIX / name).write_text("{}")
    with pytest.raises(ValueError, match="allowlist"):
        package.sources(source_tree)


def test_missing_runtime_is_rejected(source_tree):
    (source_tree / package.PREFIX / "client.py").unlink()
    with pytest.raises(ValueError, match="allowlist"):
        package.sources(source_tree)


def test_invalid_manifest_is_rejected(source_tree):
    (source_tree / package.PREFIX / "manifest.json").write_text(
        '{"domain": "wrong", "version": "0.1.0"}'
    )
    with pytest.raises(ValueError, match="domain/version"):
        package.sources(source_tree)


@pytest.mark.parametrize(
    "name", ["brand/private.txt", "brand/cookies.json", "brand/unreviewed.png"]
)
def test_unreviewed_brand_assets_fail_closed(source_tree, name):
    (source_tree / package.PREFIX / name).write_text("synthetic secret")
    with pytest.raises(ValueError, match="Brand files.*allowlist"):
        package.sources(source_tree)


@pytest.mark.parametrize("name", package.BRAND_FILES)
def test_missing_brand_asset_fails_closed(source_tree, name):
    (source_tree / package.PREFIX / name).unlink()
    with pytest.raises(ValueError, match="Brand files.*allowlist"):
        package.sources(source_tree)


@pytest.mark.parametrize("condition", ["fake", "trailing", "wrong-size", "corrupt"])
def test_invalid_brand_png_fails_closed(source_tree, condition):
    path = source_tree / package.PREFIX / "brand/icon.png"
    data = path.read_bytes()
    if condition == "fake":
        data = b"not really a png"
    elif condition == "trailing":
        data += b"synthetic secret"
    elif condition == "wrong-size":
        data = (ROOT / package.PREFIX / "brand/icon@2x.png").read_bytes()
    else:
        data = data[:100] + bytes([data[100] ^ 1]) + data[101:]
    path.write_bytes(data)
    with pytest.raises(ValueError, match="PNG"):
        package.sources(source_tree)


def test_package_check_cli():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/package.py"), "--check"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Validated" in result.stdout


@pytest.mark.parametrize("member", ["../escape.py", "unexpected.txt"])
def test_archive_verification_rejects_extra_members(source_tree, tmp_path, member):
    output = tmp_path / "loseit.zip"
    package.build(source_tree, output)
    with ZipFile(output, "a") as archive:
        archive.writestr(member, "unexpected")
    with pytest.raises(ValueError, match="members"):
        package.verify(output, package.sources(source_tree))


def test_archive_verification_rejects_content_changes(source_tree, tmp_path):
    output = tmp_path / "loseit.zip"
    package.build(source_tree, output)
    expected = package.sources(source_tree)
    expected[package.PREFIX + "client.py"] = b"changed"
    with pytest.raises(ValueError, match="content mismatch"):
        package.verify(output, expected)


@pytest.mark.parametrize(
    "metadata",
    [
        "timestamp",
        "permissions",
        "platform",
        "compression",
        "extra",
        "comment",
        "archive-comment",
    ],
)
def test_archive_verification_rejects_changed_metadata(source_tree, tmp_path, metadata):
    """Identical payloads must not hide non-deterministic or private ZIP metadata."""
    output = tmp_path / "loseit.zip"
    altered = tmp_path / "altered.zip"
    package.build(source_tree, output)
    with ZipFile(output) as original, ZipFile(altered, "w") as archive:
        for index, member in enumerate(original.infolist()):
            data = original.read(member)
            if index == 0:
                if metadata == "timestamp":
                    member.date_time = (2026, 1, 1, 0, 0, 0)
                elif metadata == "permissions":
                    member.external_attr = 0o100755 << 16
                elif metadata == "platform":
                    member.create_system = 0
                elif metadata == "compression":
                    member.compress_type = ZIP_STORED
                elif metadata == "extra":
                    member.extra = b"\xfe\xca\x04\x00test"
                elif metadata == "comment":
                    member.comment = b"synthetic private metadata"
                else:
                    archive.comment = b"synthetic private metadata"
            archive.writestr(member, data)
    with pytest.raises(ValueError, match="metadata"):
        package.verify(altered, package.sources(source_tree))


@pytest.mark.parametrize("output", ["custom_components/loseit/output.zip", "bad.txt"])
def test_invalid_output_location_rejected(source_tree, output):
    with pytest.raises(ValueError, match="Output"):
        package.build(source_tree, source_tree / output)
