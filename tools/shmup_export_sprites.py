"""
shmup_export_sprites.py - helper to integrate loose PNG sprites into the NGPC pipeline.

Source folder (user art):
  GraphX/tile 8x8/sprites/

This script:
  - Pads each frame to a multiple of 8 pixels (centered, transparent background)
  - Packs frames into a horizontal spritesheet
  - Runs tools/ngpc_sprite_export.py to generate GraphX/*_mspr.c/.h

By default it exports the core shmup demo assets (player, enemies, bullets, FX,
trails, asteroids, and UI banners).
Use --all to also export extra sprites (boss, drops, extra bullets, etc.).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


def _round_up_8(v: int) -> int:
    return (v + 7) & ~7


def _pad_center(img: Image.Image, w: int, h: int) -> Image.Image:
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox = (w - img.size[0]) // 2
    oy = (h - img.size[1]) // 2
    out.paste(img, (ox, oy), img)
    return out


def _write_sheet(frames: list[Image.Image], frame_w: int, frame_h: int, out_path: Path) -> None:
    sheet = Image.new("RGBA", (frame_w * len(frames), frame_h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * frame_w, 0), f)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


_RE_TILES = re.compile(r"^Tiles:\s+(\d+)\s+unique\b")
_RE_PALS = re.compile(r"^Palettes:\s+(\d+)\b")


@dataclass(frozen=True)
class ExportResult:
    tiles_unique: int
    palettes: int


def _run_export(
    project_root: Path,
    exporter: Path,
    sheet_path: Path,
    out_c: Path,
    name: str,
    frame_w: int,
    frame_h: int,
    frame_count: int,
    anim_duration: int,
    tile_base: int,
    pal_base: int,
    fixed_palette: list[int] | None = None,
) -> ExportResult:
    cmd = [
        sys.executable,
        str(exporter),
        str(sheet_path),
        "-o",
        str(out_c),
        "-n",
        name,
        "--frame-w",
        str(frame_w),
        "--frame-h",
        str(frame_h),
        "--tile-base",
        str(tile_base),
        "--pal-base",
        str(pal_base),
        "--anim-duration",
        str(anim_duration),
        "--header",
    ]
    if fixed_palette is not None:
        if len(fixed_palette) != 4:
            raise ValueError("fixed_palette must contain exactly 4 RGB444 u16 entries.")
        cmd += ["--fixed-palette", ",".join(f"0x{c:04X}" for c in fixed_palette)]
    if frame_count > 0:
        cmd += ["--frame-count", str(frame_count)]

    r = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        raise SystemExit(r.returncode)

    tiles_unique = 0
    palettes = 0
    for line in (r.stdout or "").splitlines():
        m = _RE_TILES.match(line.strip())
        if m:
            tiles_unique = int(m.group(1))
        m = _RE_PALS.match(line.strip())
        if m:
            palettes = int(m.group(1))

    if tiles_unique <= 0:
        raise RuntimeError("Failed to parse tile count from exporter output.")
    if palettes <= 0:
        raise RuntimeError("Failed to parse palette count from exporter output.")

    print(r.stdout.rstrip())
    return ExportResult(tiles_unique=tiles_unique, palettes=palettes)


def _load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def _sheet_from_files(paths: list[Path], frame_w: int, frame_h: int, sheet_path: Path) -> int:
    frames: list[Image.Image] = []
    for p in paths:
        frames.append(_pad_center(_load_rgba(p), frame_w, frame_h))
    _write_sheet(frames, frame_w, frame_h, sheet_path)
    return len(frames)


def _sheet_from_images(frames: list[Image.Image], frame_w: int, frame_h: int, sheet_path: Path) -> int:
    padded = [_pad_center(f, frame_w, frame_h) for f in frames]
    _write_sheet(padded, frame_w, frame_h, sheet_path)
    return len(padded)


def _split_two_layers_global(frames: list[Image.Image], frame_w: int, frame_h: int) -> tuple[list[Image.Image], list[Image.Image]]:
    """
    Split frames into 2 layers (A + B) using a GLOBAL 3+3 color split.

    This keeps palette usage low (typically 1 palette per layer) which is crucial
    on NGPC (16 sprite palettes total). Intended for "6 colors via 2 sprites"
    style ships.
    """
    freq: dict[tuple[int, int, int], int] = {}
    padded: list[Image.Image] = []
    for f in frames:
        pf = _pad_center(f, frame_w, frame_h)
        padded.append(pf)
        for r, g, b, a in pf.getdata():
            if a < 128:
                continue
            key = (r, g, b)
            freq[key] = freq.get(key, 0) + 1

    ordered = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    colors = [c for c, _ in ordered]
    if len(colors) > 6:
        raise SystemExit(f"Sprite uses {len(colors)} opaque colors (>6). Reduce colors or split manually.")

    keep = set(colors[:3])

    layer_a: list[Image.Image] = []
    layer_b: list[Image.Image] = []
    for pf in padded:
        aimg = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        bimg = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        px = pf.load()
        apx = aimg.load()
        bpx = bimg.load()
        for y in range(frame_h):
            for x in range(frame_w):
                r, g, b, aa = px[x, y]
                if aa < 128:
                    continue
                if (r, g, b) in keep:
                    apx[x, y] = (r, g, b, aa)
                else:
                    bpx[x, y] = (r, g, b, aa)
        layer_a.append(aimg)
        layer_b.append(bimg)

    return layer_a, layer_b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Export extra sprites not used by the demo yet")
    ap.add_argument("--asteroids", action="store_true", help="(Deprecated) Asteroids are exported by default")
    ap.add_argument("--no-asteroids", action="store_true", help="Skip asteroid sprites (if you removed them from the game)")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "GraphX" / "tile 8x8" / "sprites"
    gen_dir = project_root / "GraphX" / "_shmup_gen"
    exporter = project_root / "tools" / "ngpc_sprite_export.py"
    out_dir = project_root / "GraphX"

    if not src_dir.exists():
        print(f"Source folder not found: {src_dir}", file=sys.stderr)
        return 2

    # Tiles 0-31 reserved, 32-127 sysfont. Keep shmup sprite tiles away from
    # scroll plane backgrounds by default (background demo uses tile_base=128).
    tile_base = 256
    pal_base = 0

    def export_sheet(
        name: str,
        sheet_path: Path,
        frame_w: int,
        frame_h: int,
        frame_count: int,
        anim_duration: int,
    ) -> None:
        nonlocal tile_base, pal_base
        out_c = out_dir / f"{name}_mspr.c"

        res = _run_export(
            project_root=project_root,
            exporter=exporter,
            sheet_path=sheet_path,
            out_c=out_c,
            name=name,
            frame_w=frame_w,
            frame_h=frame_h,
            frame_count=frame_count,
            anim_duration=anim_duration,
            tile_base=tile_base,
            pal_base=pal_base,
        )

        tile_base += res.tiles_unique
        pal_base += res.palettes
        if tile_base > 512:
            raise SystemExit(f"Tile overflow: reached tile_base={tile_base} (>512).")
        if pal_base > 16:
            raise SystemExit(f"Palette overflow: reached pal_base={pal_base} (>16).")

    def export_sheet_reuse_palette(
        name: str,
        sheet_path: Path,
        frame_w: int,
        frame_h: int,
        frame_count: int,
        anim_duration: int,
        shared_pal_base: int,
        fixed_palette: list[int] | None = None,
    ) -> None:
        """
        Export sprite tiles normally, but force a fixed sprite palette base.

        This is useful when multiple sprites are authored to use the same colors
        (ex: asteroids). It saves NGPC sprite palette slots (16 total).
        """
        nonlocal tile_base, pal_base
        out_c = out_dir / f"{name}_mspr.c"

        res = _run_export(
            project_root=project_root,
            exporter=exporter,
            sheet_path=sheet_path,
            out_c=out_c,
            name=name,
            frame_w=frame_w,
            frame_h=frame_h,
            frame_count=frame_count,
            anim_duration=anim_duration,
            tile_base=tile_base,
            pal_base=shared_pal_base,
            fixed_palette=fixed_palette,
        )

        tile_base += res.tiles_unique
        # IMPORTANT: do not advance pal_base; the palette slot is shared.
        if tile_base > 512:
            raise SystemExit(f"Tile overflow: reached tile_base={tile_base} (>512).")
        if shared_pal_base + res.palettes > 16:
            raise SystemExit(f"Palette overflow: shared_pal_base={shared_pal_base}, palettes={res.palettes} (>16).")

    # ---- Core demo assets ----

    # Player ship uses up to 6 colors in a tile; export as 2 layers (A + B).
    ship_paths = [
        src_dir / "Player_ship_up.png",
        src_dir / "Player_ship_normal.png",
        src_dir / "Player_ship_down.png",
    ]
    ship_frames = [_load_rgba(p) for p in ship_paths]
    ship_a, ship_b = _split_two_layers_global(ship_frames, 16, 16)

    ship_a_sheet = gen_dir / "shmup_player_a_sheet.png"
    ship_b_sheet = gen_dir / "shmup_player_b_sheet.png"
    ship_count = _sheet_from_images(ship_a, 16, 16, ship_a_sheet)
    _sheet_from_images(ship_b, 16, 16, ship_b_sheet)

    ship_a_shared_pal_base = pal_base
    export_sheet("shmup_player_a", ship_a_sheet, 16, 16, ship_count, 6)
    ship_b_shared_pal_base = pal_base
    export_sheet("shmup_player_b", ship_b_sheet, 16, 16, ship_count, 6)

    def parse_pal4_from_mspr_c(mspr_c_path: Path, symbol: str) -> list[int]:
        txt = mspr_c_path.read_text(encoding="utf-8", errors="replace")
        marker = f"const u16 {symbol}_palettes[]"
        start = txt.find(marker)
        if start < 0:
            raise RuntimeError(f"Cannot find {marker} in {mspr_c_path}")
        brace = txt.find("{", start)
        if brace < 0:
            raise RuntimeError(f"Cannot find palette initializer '{{' in {mspr_c_path}")
        after = txt[brace:]
        words: list[int] = []
        i = 0
        while i < len(after) and len(words) < 4:
            j = after.find("0x", i)
            if j < 0:
                break
            w = after[j + 2 : j + 6]
            if len(w) == 4 and all(ch in "0123456789abcdefABCDEF" for ch in w):
                words.append(int(w, 16))
            i = j + 2
        if len(words) < 4:
            raise RuntimeError(f"Cannot parse 4 palette words from {mspr_c_path}")
        return words[:4]

    ship_a_pal4 = parse_pal4_from_mspr_c(out_dir / "shmup_player_a_mspr.c", "shmup_player_a")
    ship_b_pal4 = parse_pal4_from_mspr_c(out_dir / "shmup_player_b_mspr.c", "shmup_player_b")

    enemy1_sheet = gen_dir / "shmup_enemy1_sheet.png"
    export_sheet("shmup_enemy1", enemy1_sheet, 8, 8, _sheet_from_files([src_dir / "ennemi_1.png"], 8, 8, enemy1_sheet), 6)

    enemy2_sheet = gen_dir / "shmup_enemy2_sheet.png"
    export_sheet("shmup_enemy2", enemy2_sheet, 8, 8, _sheet_from_files([src_dir / "ennemi_2.png"], 8, 8, enemy2_sheet), 6)

    enemy3_sheet = gen_dir / "shmup_enemy3_sheet.png"
    export_sheet("shmup_enemy3", enemy3_sheet, 8, 8, _sheet_from_files([src_dir / "ennemi_3.png"], 8, 8, enemy3_sheet), 6)

    bullet_sheet = gen_dir / "shmup_bullet_sheet.png"
    export_sheet("shmup_bullet", bullet_sheet, 8, 8, _sheet_from_files([src_dir / "tir_basique.png"], 8, 8, bullet_sheet), 3)

    # Nemesis OPTION (satellite). This sprite uses colors from BOTH ship palettes
    # (A+B), so we export it as two overlayed 8x8 sprites to reuse both palettes.
    if (src_dir / "powerup_option.png").exists():
        opt = _load_rgba(src_dir / "powerup_option.png")
        opt = _pad_center(opt, 8, 8)

        def rgb444(px: tuple[int, int, int, int]) -> int:
            r, g, b, a = px
            if a < 128:
                return 0
            return ((r >> 4) & 0xF) | (((g >> 4) & 0xF) << 4) | (((b >> 4) & 0xF) << 8)

        # Color routing: 0x0219 is the ship's dark red (in palette A). The other
        # option colors (0x0657 gray, 0x0112 dark) live in palette B.
        opt_a = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        opt_b = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        src_px = opt.load()
        a_px = opt_a.load()
        b_px = opt_b.load()
        for y in range(8):
            for x in range(8):
                p = src_px[x, y]
                if p[3] < 128:
                    continue
                if rgb444(p) == 0x0219:
                    a_px[x, y] = p
                else:
                    b_px[x, y] = p

        s = gen_dir / "shmup_option_a_sheet.png"
        _sheet_from_images([opt_a], 8, 8, s)
        export_sheet_reuse_palette(
            "shmup_option_a",
            s,
            8,
            8,
            1,
            1,
            ship_a_shared_pal_base,
            fixed_palette=ship_a_pal4,
        )

        s = gen_dir / "shmup_option_b_sheet.png"
        _sheet_from_images([opt_b], 8, 8, s)
        export_sheet_reuse_palette(
            "shmup_option_b",
            s,
            8,
            8,
            1,
            1,
            ship_b_shared_pal_base,
            fixed_palette=ship_b_pal4,
        )

    exp_sheet = gen_dir / "shmup_explosion_sheet.png"
    export_sheet(
        "shmup_explosion",
        exp_sheet,
        8,
        8,
        _sheet_from_files([src_dir / "explosion_f_1.png", src_dir / "explosion_f_2.png", src_dir / "explosion_f_3.png"], 8, 8, exp_sheet),
        3,
    )

    trail_sheet = gen_dir / "shmup_trail_sheet.png"
    trail_shared_pal_base = pal_base
    export_sheet(
        "shmup_trail",
        trail_sheet,
        8,
        8,
        _sheet_from_files([src_dir / "traine_f_1.png", src_dir / "traine_f_2.png", src_dir / "traine_f_3.png"], 8, 8, trail_sheet),
        2,
    )

    # Fat enemy shares the same palette as the player trail (authored with same colors).
    if (src_dir / "ennemi_5_fat.png").exists():
        s = gen_dir / "shmup_enemy5_fat_sheet.png"
        export_sheet_reuse_palette(
            "shmup_enemy5_fat",
            s,
            16,
            16,
            _sheet_from_files([src_dir / "ennemi_5_fat.png"], 16, 16, s),
            6,
            trail_shared_pal_base,
        )

    # Optional alternative trail (2 frames, already 8x8).
    if (src_dir / "traine_v2_f_1.png").exists() and (src_dir / "traine_v2_f_2.png").exists():
        trail2_sheet = gen_dir / "shmup_trail2_sheet.png"
        export_sheet(
            "shmup_trail2",
            trail2_sheet,
            8,
            8,
            _sheet_from_files([src_dir / "traine_v2_f_1.png", src_dir / "traine_v2_f_2.png"], 8, 8, trail2_sheet),
            3,
        )

    export_asteroids = (not args.no_asteroids)

    if export_asteroids:
        # Asteroids (pad to friendly metasprite bounds).
        s = gen_dir / "shmup_ast1_sheet.png"
        ast_shared_pal_base = pal_base
        export_sheet("shmup_ast1", s, 16, 16, _sheet_from_files([src_dir / "asteroide_1.png"], 16, 16, s), 6)
        s = gen_dir / "shmup_ast2_sheet.png"
        export_sheet_reuse_palette("shmup_ast2", s, 16, 16, _sheet_from_files([src_dir / "asteroide_2.png"], 16, 16, s), 6, ast_shared_pal_base)
        s = gen_dir / "shmup_ast3_sheet.png"
        export_sheet_reuse_palette("shmup_ast3", s, 8, 16, _sheet_from_files([src_dir / "asteroide_3.png"], 8, 16, s), 6, ast_shared_pal_base)
        s = gen_dir / "shmup_ast4_sheet.png"
        export_sheet_reuse_palette("shmup_ast4", s, 16, 8, _sheet_from_files([src_dir / "asteroide_4_petit.png"], 16, 8, s), 6, ast_shared_pal_base)
        s = gen_dir / "shmup_ast5_sheet.png"
        export_sheet_reuse_palette("shmup_ast5", s, 8, 8, _sheet_from_files([src_dir / "asteroide_5_petit.png"], 8, 8, s), 6, ast_shared_pal_base)

    # UI banners (sprites).
    s = gen_dir / "ui_start_sheet.png"
    ui_start_shared_pal_base = pal_base
    export_sheet("ui_start", s, 48, 8, _sheet_from_files([src_dir / "START (48 x 8).png"], 48, 8, s), 30)
    s = gen_dir / "ui_game_over_sheet.png"
    export_sheet("ui_game_over", s, 72, 8, _sheet_from_files([src_dir / "GAME_OVER (72 x 8).png"], 72, 8, s), 30)

    # HUD digits (0-9) share the same palette as START (green).
    digit_paths = [src_dir / f"{i}.png" for i in range(10)]
    if all(p.exists() for p in digit_paths):
        s = gen_dir / "ui_digits_sheet.png"
        export_sheet_reuse_palette(
            "ui_digits",
            s,
            8,
            8,
            _sheet_from_files(digit_paths, 8, 8, s),
            1,
            ui_start_shared_pal_base,
        )

    # Nemesis-style power-up meter cursor letters (S P D L O) also share START palette.
    pu_paths = [
        src_dir / "power_up_s.png",
        src_dir / "power_up_p.png",
        src_dir / "power_up_d.png",
        src_dir / "power_up_l.png",
        src_dir / "power_up_o.png",
    ]
    if all(p.exists() for p in pu_paths):
        s = gen_dir / "ui_powerup_sheet.png"
        export_sheet_reuse_palette(
            "ui_powerup",
            s,
            8,
            8,
            _sheet_from_files(pu_paths, 8, 8, s),
            1,
            ui_start_shared_pal_base,
        )

    # Nemesis-style capsule drop. It shares the same palette as START to save palette slots.
    if (src_dir / "drop_final.png").exists():
        s = gen_dir / "shmup_drop_final_sheet.png"
        export_sheet_reuse_palette(
            "shmup_drop_final",
            s,
            8,
            8,
            _sheet_from_files([src_dir / "drop_final.png"], 8, 8, s),
            6,
            ui_start_shared_pal_base,
        )

    if args.all:
        # Extra drop icons (future UI / wheel icons).
        s = gen_dir / "shmup_drop1_sheet.png"
        export_sheet("shmup_drop1", s, 8, 8, _sheet_from_files([src_dir / "drop_1.png"], 8, 8, s), 6)
        s = gen_dir / "shmup_drop2_sheet.png"
        export_sheet("shmup_drop2", s, 8, 8, _sheet_from_files([src_dir / "drop_2.png"], 8, 8, s), 6)
        s = gen_dir / "shmup_drop3_sheet.png"
        export_sheet("shmup_drop3", s, 8, 8, _sheet_from_files([src_dir / "drop_3.png"], 8, 8, s), 6)

        # Small enemy bullets (pad to 8x8).
        s = gen_dir / "shmup_enemy_bullet1_sheet.png"
        export_sheet("shmup_enemy_bullet1", s, 8, 8, _sheet_from_files([src_dir / "ennemi_shoot_t_1.png"], 8, 8, s), 3)
        s = gen_dir / "shmup_enemy_bullet2_sheet.png"
        export_sheet("shmup_enemy_bullet2", s, 8, 8, _sheet_from_files([src_dir / "ennemi_shoot_t_2.png"], 8, 8, s), 3)
        s = gen_dir / "shmup_enemy_bullet3_sheet.png"
        export_sheet("shmup_enemy_bullet3", s, 8, 8, _sheet_from_files([src_dir / "ennemi_shoot_t_3.png"], 8, 8, s), 3)

        # Other player bullets.
        s = gen_dir / "shmup_bullet2_sheet.png"
        export_sheet("shmup_bullet2", s, 8, 8, _sheet_from_files([src_dir / "tir_double.png"], 8, 8, s), 3)
        s = gen_dir / "shmup_bullet3_sheet.png"
        export_sheet("shmup_bullet3", s, 8, 8, _sheet_from_files([src_dir / "tir_triple.png"], 8, 8, s), 3)

        s = gen_dir / "shmup_boss1_sheet.png"
        export_sheet("shmup_boss1", s, 24, 32, _sheet_from_files([src_dir / "boss-1.png"], 24, 32, s), 6)
        if (src_dir / "BOSS_niveau_2.png").exists():
            s = gen_dir / "shmup_boss2_sheet.png"
            export_sheet_reuse_palette(
                "shmup_boss2",
                s,
                32,
                32,
                _sheet_from_files([src_dir / "BOSS_niveau_2.png"], 32, 32, s),
                6,
                14,
            )

    print(f"Done. Next tile_base={tile_base}, pal_base={pal_base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
