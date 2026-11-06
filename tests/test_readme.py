"""Keep the compact README's local chip row accessible and truthful."""

import json
import re
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


def test_readme_local_chip_order_accessibility_and_style():
    readme = (ROOT / "README.md").read_text()
    chips = re.findall(r"\[!\[([^\]]+)\]\(([^)]+)\)\]\(([^)]+)\)", readme)
    expected = [
        ("ci", "CI: workflow", "#64748b"),
        ("compatibility", "HA tested: 2026.10.4", "#0369a1"),
        ("license", "License: MIT", "#2563eb"),
        ("distribution", "Distribution: HACS custom", "#047857"),
    ]
    assert len(chips) == len(expected)
    for (alt, asset, link), (name, label, color) in zip(chips, expected, strict=True):
        assert alt == label
        assert asset == f"docs/badges/{name}.svg"
        assert (
            link.startswith("https://github.com/ColeMundus/ha-loseit/")
            or (ROOT / link.split("#")[0]).is_file()
        )
        svg = ElementTree.parse(ROOT / asset).getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        assert svg.attrib["height"] == "20"
        assert svg.attrib["role"] == "img"
        assert svg.attrib["aria-label"] == label
        title = svg.find("svg:title", ns)
        assert title is not None and title.text == label
        assert {r.attrib["fill"] for r in svg.findall(".//svg:rect", ns)} >= {
            "#555",
            color,
        }
        assert any(r.attrib.get("rx") == "3" for r in svg.findall(".//svg:rect", ns))
        texts = svg.findall(".//svg:text", ns)
        assert texts
        for text in texts:
            assert text.attrib["fill"] == "#fff"
            assert text.attrib["font-size"] == "11"
            assert text.attrib["font-family"] == "DejaVu Sans,Verdana,sans-serif"
        assert not svg.findall(".//svg:linearGradient", ns)
        assert not svg.findall(".//svg:filter", ns)
        assert not svg.findall(".//svg:image", ns)
    assert "img.shields.io" not in readme


def test_readme_compact_official_icon_and_stable_installation():
    readme = (ROOT / "README.md").read_text()
    icon = re.search(r'<img src="([^"]+)"[^>]+>', readme)
    assert icon is not None
    assert icon.group(1) == "custom_components/loseit/brand/icon.png"
    assert (ROOT / icon.group(1)).is_file()
    assert 'alt="Official Lose It! app icon"' in icon.group()
    assert 'width="64"' in icon.group() and 'height="64"' in icon.group()
    assert "**0.1.0**" in readme
    assert "default stable release" in readme
    installation = (ROOT / "docs/installation.md").read_text()
    for text in (readme, installation):
        assert "beta" not in text.lower()
        assert "0.1.0b1" not in text
    assert "default stable release" in installation
    assert json.loads((ROOT / "hacs.json").read_text())["name"] == "Lose It!"
    assert "Custom repositories" in readme
    assert "not in the default catalog" in readme
    assert "private" not in readme
    assert len(readme.splitlines()) <= 55
