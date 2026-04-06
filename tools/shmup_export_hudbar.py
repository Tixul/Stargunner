"""
shmup_export_hudbar.py - export bottom HUD bar tilemap for the shmup demo.

Input artwork:
  GraphX/hud_vide_bas ecran.png  (160x16)

The NGPC tilemap pipeline requires <=3 visible colors per 8x8 tile.
The provided HUD bar uses 4 colors; a few tiles combine all 4, which
triggers dual-layer auto-split in tools/ngpc_tilemap.py.

This script remaps the small accent green into an existing gray so the
HUD bar becomes single-layer, then runs tools/ngpc_tilemap.py.

Output:
  GraphX/shmup_hudbar.c + GraphX/shmup_hudbar.h
  GraphX/_shmup_gen/shmup_hudbar_3col.png
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    src = project_root / "GraphX" / "hud_vide_bas ecran.png"
    gen = project_root / "GraphX" / "_shmup_gen" / "shmup_hudbar_3col.png"
    out_c = project_root / "GraphX" / "shmup_hudbar.c"
    tool = project_root / "tools" / "ngpc_tilemap.py"

    if not src.exists():
        print(f"Missing input: {src}", file=sys.stderr)
        return 2

    img = Image.open(src).convert("RGBA")
    if img.size != (160, 16):
        print(f"Expected 160x16px, got {img.size}.", file=sys.stderr)
        return 2

    # 4-color source palette; merge the least-used accent green into gray.
    # (This keeps the look while guaranteeing <=3 visible colors per tile.)
    green = (106, 190, 48)
    gray = (105, 106, 106)

    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            if (r, g, b) == green:
                px[x, y] = (gray[0], gray[1], gray[2], a)

    gen.parent.mkdir(parents=True, exist_ok=True)
    img.save(gen)

    cmd = [
        sys.executable,
        str(tool),
        str(gen),
        "-o",
        str(out_c),
        "-n",
        "shmup_hudbar",
        "--header",
    ]
    r = subprocess.run(cmd, cwd=str(project_root), text=True, check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())

