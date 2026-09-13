#!/usr/bin/env python3
"""Generate deterministic Codex plugin assets from the approved ProcessOn SVG."""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_svg(source: Path) -> tuple[int, int]:
    """Return the source viewBox dimensions or raise an actionable error."""
    if not source.is_file():
        raise FileNotFoundError(f"SVG source does not exist: {source}")

    root = ET.fromstring(source.read_bytes())
    view_box = root.attrib.get("viewBox", "").split()
    if len(view_box) != 4:
        raise ValueError(f"SVG source has no valid viewBox: {source}")

    width = float(view_box[2])
    height = float(view_box[3])
    if width <= 0 or height <= 0:
        raise ValueError(f"SVG viewBox dimensions must be positive: {source}")
    return math.ceil(width), math.ceil(height)


def copy_source_svg(source: Path, destination: Path) -> None:
    """Copy the approved SVG bytes unchanged."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copyfile(source, destination)


def render_square_png(
    source: Path,
    destination: Path,
    size: int,
    background: str,
) -> None:
    """Render a centered, aspect-preserving SVG on a square color field."""
    if size <= 0:
        raise ValueError("PNG size must be positive")
    validate_svg(source)

    rsvg = shutil.which("rsvg-convert")
    magick = shutil.which("magick")
    if not rsvg or not magick:
        raise RuntimeError(
            "Asset generation requires existing rsvg-convert and ImageMagick "
            "executables; install them explicitly before retrying."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    inner_width = max(1, round(size * 0.86))
    with tempfile.TemporaryDirectory(prefix="processon-assets-") as temp_dir:
        rendered = Path(temp_dir) / "mark.png"
        subprocess.run(
            [rsvg, "--width", str(inner_width), "--output", str(rendered), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                magick,
                "-size",
                f"{size}x{size}",
                f"xc:{background}",
                str(rendered),
                "-gravity",
                "center",
                "-composite",
                "-strip",
                str(destination),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


def generate_assets(source: Path, assets_dir: Path) -> None:
    """Copy the approved vector and generate all manifest PNG assets."""
    validate_svg(source)
    vector = assets_dir / "logo.svg"
    copy_source_svg(source, vector)
    render_square_png(vector, assets_dir / "logo.png", 512, "#2F80ED")
    render_square_png(vector, assets_dir / "logo-dark.png", 512, "#111827")
    render_square_png(vector, assets_dir / "composer-icon.png", 64, "#2F80ED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("assets_dir", type=Path)
    args = parser.parse_args()
    generate_assets(args.source, args.assets_dir)
    print(f"Generated ProcessOn assets in {args.assets_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
