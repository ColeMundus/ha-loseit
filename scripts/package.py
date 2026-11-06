"""Build/check a deterministic manual-install ZIP, not a HACS zip_release asset."""

import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "custom_components/loseit/"
# Explicitly reviewed runtime allowlist; update alongside added/split modules.
RUNTIME_FILES = (
    "__init__.py",
    "client.py",
    "config_flow.py",
    "const.py",
    "coordinator.py",
    "diagnostics.py",
    "gwt.py",
    "models.py",
    "protocol.py",
    "request_gate.py",
    "schemas.py",
    "sensor.py",
    "snapshot.py",
    "manifest.json",
    "strings.json",
    "translations/en.json",
)
BRAND_FILES = (
    "brand/icon.png",
    "brand/icon@2x.png",
    "brand/NOTICE.md",
)
NOTICES = ("LICENSE", "THIRD_PARTY_NOTICES.md")


def validate_png(data: bytes, size: int) -> None:
    """Validate bounded RGBA exports, rejecting metadata/private trailing payloads."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) > 1_000_000:
        raise ValueError("Invalid brand PNG signature/size")
    offset = 8
    chunks = []
    pixels = bytearray()
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated brand PNG")
        length = int.from_bytes(data[offset : offset + 4])
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        end = offset + 12 + length
        crc = data[offset + 8 + length : end]
        if end > len(data) or zlib.crc32(kind + payload) != int.from_bytes(crc):
            raise ValueError("Invalid brand PNG checksum")
        if kind not in (b"IHDR", b"bKGD", b"IDAT", b"IEND"):
            raise ValueError("Unreviewed brand PNG metadata")
        if kind == b"IHDR" and payload != struct.pack(
            ">IIBBBBB", size, size, 8, 6, 0, 0, 0
        ):
            raise ValueError("Brand PNG must be correctly sized 8-bit RGBA")
        if kind == b"IDAT":
            pixels.extend(payload)
        if kind == b"IEND" and (payload or end != len(data)):
            raise ValueError("Invalid brand PNG ending")
        chunks.append(kind)
        offset = end
    if (
        not chunks
        or chunks[0] != b"IHDR"
        or chunks[-1] != b"IEND"
        or chunks.count(b"IHDR") != 1
        or chunks.count(b"IEND") != 1
    ):
        raise ValueError("Invalid brand PNG structure")
    decoder = zlib.decompressobj()
    expected = size * (1 + size * 4)
    try:
        raw = decoder.decompress(pixels, expected + 1)
    except zlib.error as err:
        raise ValueError("Invalid brand PNG pixels") from err
    if len(raw) != expected or not decoder.eof or decoder.unused_data:
        raise ValueError("Invalid brand PNG pixel length")
    if any(raw[row * (1 + size * 4)] > 4 for row in range(size)):
        raise ValueError("Invalid brand PNG row filter")


def sources(root: Path) -> dict[str, bytes]:
    """Collect runtime files and required root notices; reject linked inputs."""
    integration = root / "custom_components" / "loseit"
    if integration.is_symlink() or integration.parent.is_symlink():
        raise ValueError("Integration directory must not be a symlink")
    paths = [integration / name for name in RUNTIME_FILES]
    translations = integration / "translations"
    if translations.is_symlink():
        raise ValueError("Translations directory must not be a symlink")
    discovered = {
        path.relative_to(integration).as_posix()
        for pattern in ("*.py", "*.json", "translations/*.json")
        for path in integration.glob(pattern)
    }
    if discovered != set(RUNTIME_FILES):
        raise ValueError("Runtime files differ from the reviewed packaging allowlist")
    result = {}
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or linked runtime file: {path.name}")
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        result[path.relative_to(root).as_posix()] = path.read_bytes()
    brand = integration / "brand"
    if brand.is_symlink() or any(path.is_symlink() for path in brand.rglob("*")):
        raise ValueError("Brand directory/files must not be symlinks")
    discovered_brand = {
        path.relative_to(integration).as_posix()
        for path in brand.rglob("*")
        if path.is_file()
    }
    if discovered_brand != set(BRAND_FILES):
        raise ValueError("Brand files differ from the reviewed packaging allowlist")
    for name in BRAND_FILES:
        path = integration / name
        data = path.read_bytes()
        if not data.strip():
            raise ValueError("Empty brand asset")
        if path.suffix == ".png":
            validate_png(data, 512 if "@2x" in name else 256)
        result[PREFIX + name] = data
    manifest = json.loads(result[PREFIX + "manifest.json"])
    if manifest["domain"] != "loseit" or not manifest.get("version"):
        raise ValueError("Invalid integration domain/version")
    for name in NOTICES:
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.read_bytes().strip():
            raise ValueError(f"Missing, empty or linked distribution notice: {name}")
        # Keep notices with the component, never overwrite HA configuration-root files.
        result[PREFIX + name] = path.read_bytes()
    return dict(sorted(result.items()))


def verify(output: Path, expected: dict[str, bytes]) -> None:
    """Verify integrity, member names, duplicates and every byte against sources."""
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt installation ZIP")
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Unexpected or duplicate installation ZIP members")
        if archive.comment or any(
            member.date_time != (1980, 1, 1, 0, 0, 0)
            or member.create_system != 3
            or member.external_attr != 0o100644 << 16
            or member.compress_type != ZIP_DEFLATED
            or member.extra
            or member.comment
            for member in archive.infolist()
        ):
            raise ValueError("Unexpected installation ZIP metadata")
        if any(archive.read(name) != data for name, data in expected.items()):
            raise ValueError("Installation ZIP content mismatch")


def build(root: Path, output: Path) -> None:
    """Write an installation archive and standard SHA256SUMS companion."""
    expected = sources(root)
    output = output.resolve()
    if output.suffix != ".zip" or output.is_relative_to(root / "custom_components"):
        raise ValueError("Output must be a .zip outside custom_components")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in expected.items():
            member = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = ZIP_DEFLATED
            member.create_system = 3
            member.external_attr = 0o100644 << 16
            archive.writestr(member, data)
    verify(output, expected)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    (output.parent / "SHA256SUMS").write_text(
        f"{digest}  {output.name}\n", encoding="utf-8"
    )
    print(f"Packaged and verified {len(expected)} files: {output.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true", help="Validate sources only")
    args = parser.parse_args()
    if args.check:
        print(f"Validated {len(sources(ROOT))} distribution files")
    elif args.output:
        build(ROOT, args.output)
    else:
        parser.error("output is required unless --check is used")


if __name__ == "__main__":
    main()
