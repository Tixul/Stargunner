"""
shmup_export_background.py - export background tilemap for the shmup demo.

Input artwork:
  GraphX/tile 8x8/sprites/background.png  (currently 320x152)

NGPC scroll planes are 32x32 tiles max, so this script crops the background
to 256x152 (32x19 tiles) before running tools/ngpc_tilemap.py.

Output:
  GraphX/shmup_bg.c + GraphX/shmup_bg.h
  GraphX/_shmup_gen/shmup_bg_32x19_3col.png (cropped + remapped source)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    src = project_root / "GraphX" / "tile 8x8" / "sprites" / "background.png"
    gen = project_root / "GraphX" / "_shmup_gen" / "shmup_bg_32x19_3col.png"
    out_c = project_root / "GraphX" / "shmup_bg.c"
    tool = project_root / "tools" / "ngpc_tilemap.py"

    if not src.exists():
        print(f"Missing input: {src}", file=sys.stderr)
        return 2

    img = Image.open(src).convert("RGBA")
    if img.size[1] != 152:
        print(f"Expected height 152px, got {img.size}.", file=sys.stderr)
        return 2

    # Crop leftmost 256x152 (32x19 tiles).
    crop = img.crop((0, 0, 256, 152)).convert("RGBA")

    # Reduce to 3 visible colors per tile (so we can use a single scroll plane).
    # Original background uses 5 colors total; we merge the minor highlight colors.
    #
    # Keep:
    #   base = (34,32,52)
    #   blue = (42,85,207)
    #   cyan = (104,222,238)
    # Merge:
    #   (32,163,248) -> cyan
    #   (242,241,240) -> cyan
    base = (34, 32, 52)
    blue = (42, 85, 207)
    cyan = (104, 222, 238)
    merge_to_cyan = {(32, 163, 248), (242, 241, 240)}

    px = crop.load()
    for y in range(crop.size[1]):
        for x in range(crop.size[0]):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            c = (r, g, b)
            if c in merge_to_cyan:
                px[x, y] = (cyan[0], cyan[1], cyan[2], a)
            elif c == base or c == blue or c == cyan:
                continue
            else:
                # Fallback: map any unexpected color to base.
                px[x, y] = (base[0], base[1], base[2], a)
    gen.parent.mkdir(parents=True, exist_ok=True)
    crop.save(gen)

    cmd = [
        sys.executable,
        str(tool),
        str(gen),
        "-o",
        str(out_c),
        "-n",
        "shmup_bg",
        "--header",
    ]
    r = subprocess.run(cmd, cwd=str(project_root), text=True, check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
