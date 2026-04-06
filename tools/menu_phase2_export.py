"""
menu_phase2_export.py - export menu background tilemap for phase 2 artwork.

Input artwork:
  GraphX/phase_2/parralax_2eme_plan.png  (320x152, front stars)
  GraphX/phase_2/parralax_3eme_plan.png  (160x152, back planet)

Because NGPC menu screens are static tilemaps with system-font text on top,
the wide 320px star layer is center-cropped to 160x152, its black pixels are
converted to transparency, then both layers are composited before auto-split
export.

Output:
  GraphX/menu_phase2.c + GraphX/menu_phase2.h
  GraphX/_menu_gen/menu_phase2_front_crop.png
  GraphX/_menu_gen/menu_phase2_composite.png
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "GraphX" / "phase_2"
    front = src_dir / "parralax_2eme_plan.png"
    back = src_dir / "parralax_3eme_plan.png"
    gen = project_root / "GraphX" / "_menu_gen" / "menu_phase2_front_crop.png"
    comp = project_root / "GraphX" / "_menu_gen" / "menu_phase2_composite.png"
    out_c = project_root / "GraphX" / "menu_phase2.c"
    tool = project_root / "tools" / "ngpc_tilemap.py"

    if not front.exists():
        print(f"Missing input: {front}", file=sys.stderr)
        return 2
    if not back.exists():
        print(f"Missing input: {back}", file=sys.stderr)
        return 2

    front_img = Image.open(front).convert("RGBA")
    back_img = Image.open(back).convert("RGBA")

    if front_img.size != (320, 152):
        print(f"Expected 320x152 for front layer, got {front_img.size}", file=sys.stderr)
        return 2
    if back_img.size != (160, 152):
        print(f"Expected 160x152 for back layer, got {back_img.size}", file=sys.stderr)
        return 2

    crop_x = (front_img.size[0] - 160) // 2
    front_crop = front_img.crop((crop_x, 0, crop_x + 160, 152))
    front_px = front_crop.load()
    for y in range(front_crop.size[1]):
        for x in range(front_crop.size[0]):
            r, g, b, a = front_px[x, y]
            if a >= 128 and r == 0 and g == 0 and b == 0:
                front_px[x, y] = (0, 0, 0, 0)

    composite = Image.alpha_composite(back_img, front_crop)

    gen.parent.mkdir(parents=True, exist_ok=True)
    front_crop.save(gen)
    composite.save(comp)

    cmd = [
        sys.executable,
        str(tool),
        str(comp),
        "-o",
        str(out_c),
        "-n",
        "menu_phase2",
        "--header",
    ]
    r = subprocess.run(cmd, cwd=str(project_root), text=True, check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
