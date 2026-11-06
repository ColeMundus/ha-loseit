"""Official artwork retains provider provenance, not a project-art license."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from scripts import package

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / package.PREFIX / "brand"


def test_brand_allowlist_and_official_provenance():
    assert set(package.BRAND_FILES) == {
        "brand/icon.png",
        "brand/icon@2x.png",
        "brand/NOTICE.md",
    }
    assert {p.name for p in BRAND.iterdir()} == {
        Path(name).name for name in package.BRAND_FILES
    }
    notice = (BRAND / "NOTICE.md").read_text()
    assert "FitNow, Inc." in notice
    assert "https://itunes.apple.com/lookup?id=297368629&country=us" in notice
    assert "https://is1-ssl.mzstatic.com/image/thumb/" in notice
    assert "2ef8a3624b72dbcd5735e026771035ca358cccbf989f1d79064bdb2467036ea2" in notice
    assert "MIT license" in notice and "**not** this artwork" in notice
    assert "unofficial" in notice
    assert "No redrawing" in notice


@pytest.mark.parametrize(
    "name,size,digest",
    [
        (
            "icon.png",
            256,
            "cfbb87818e3d99f730bb1452d56f4c0999027554c073a0ebcbc406f2d1fc9644",
        ),
        (
            "icon@2x.png",
            512,
            "53006d7570fc5b1027ec363426491e244ddd006a4f0c6968891b9c934a444c6c",
        ),
    ],
)
def test_png_is_reviewed_official_square_rgba_without_metadata(name, size, digest):
    # Pin reviewed exports: arbitrary valid PNGs are not branding verification.
    assert hashlib.sha256((BRAND / name).read_bytes()).hexdigest() == digest
    with Image.open(BRAND / name) as image:
        image.verify()
    with Image.open(BRAND / name) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"
        assert image.size == (size, size)
        assert image.info == {}
        assert image.getchannel("A").getextrema() == (255, 255)
        colors = image.getcolors(size * size)
        assert colors is not None and len(colors) > 100


def test_source_hacs_and_manual_distribution_contain_identical_brand_files():
    sources = package.sources(ROOT)
    for name in package.BRAND_FILES:
        assert (
            sources[package.PREFIX + name]
            == (ROOT / package.PREFIX / name).read_bytes()
        )
