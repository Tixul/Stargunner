"""
menu_principal_export.py - export main menu tilemap (fond + premier plan).

Input artwork:
  GraphX/menu principal/fond.png          (160x152)
  GraphX/menu principal/premier plan.png  (160x152, alpha overlay)

This script composites the two PNGs and runs tools/ngpc_tilemap.py.
The tilemap exporter will auto-split tiles across SCR1/SCR2 when a tile
uses >3 visible colors (NGPC scroll limitation).

Output:
  GraphX/menu_principal.c + GraphX/menu_principal.h
  GraphX/_menu_gen/menu_principal_composite.png
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "GraphX" / "menu principal"
    fond = src_dir / "fond.png"
    overlay = src_dir / "premier plan.png"
    gen = project_root / "GraphX" / "_menu_gen" / "menu_principal_composite.png"
    out_c = project_root / "GraphX" / "menu_principal.c"
    tool = project_root / "tools" / "ngpc_tilemap.py"

    if not fond.exists():
        print(f"Missing input: {fond}", file=sys.stderr)
        return 2
    if not overlay.exists():
        print(f"Missing input: {overlay}", file=sys.stderr)
        return 2

    base = Image.open(fond).convert("RGBA")
    top = Image.open(overlay).convert("RGBA")
    if base.size != (160, 152) or top.size != (160, 152):
        print(f"Expected 160x152, got fond={base.size}, overlay={top.size}", file=sys.stderr)
        return 2

    comp = Image.alpha_composite(base, top)
    gen.parent.mkdir(parents=True, exist_ok=True)
    comp.save(gen)

    cmd = [
        sys.executable,
        str(tool),
        str(gen),
        "-o",
        str(out_c),
        "-n",
        "menu_principal",
        "--header",
    ]
    r = subprocess.run(cmd, cwd=str(project_root), text=True, check=False)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())

