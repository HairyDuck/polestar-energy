"""Create HACS/Home Assistant brand icons from a square source PNG.

Usage:
  python scripts/make_brand_icons.py path/to/source.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

BRAND = Path(__file__).resolve().parents[1] / "custom_components" / "polestar_energy" / "brand"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip())
    src = Path(sys.argv[1])
    if not src.is_file():
        raise SystemExit(f"Source image not found: {src}")

    BRAND.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGBA")
    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    square = img.crop((left, top, left + side, top + side))

    for size, name in (
        (256, "icon.png"),
        (512, "icon@2x.png"),
        (256, "logo.png"),
        (512, "logo@2x.png"),
        (256, "dark_icon.png"),
        (512, "dark_icon@2x.png"),
    ):
        out = square.resize((size, size), Image.Resampling.LANCZOS)
        path = BRAND / name
        out.save(path, format="PNG", optimize=True)
        print(f"{path.name}: {out.size[0]}x{out.size[1]} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
