# Guide graphique NGPC — Pipeline PNG → tilemap → affichage

Ce guide couvre le pipeline complet d'affichage : de la génération des assets
jusqu'au rendu à l'écran, avec les deux méthodes disponibles et la checklist
de diagnostic quand ça ne marche pas.

---

## 1. Pipeline complet

```
PNG source
    │
    ▼
ngpc_tilemap.py  ──►  GraphX/foo.c + foo.h
                       (tiles u16/u8, tilemap, palettes)
    │
    ▼
Code C (méthode A ou B)
    │
    ▼
Affichage écran 160×152 px
```

---

## 2. Commandes ngpc_tilemap.py

### Plein écran (intro/menu) — tiles en bytes (u8, pratique pour cc900)

```bash
python tools/ngpc_tilemap.py assets/title.png \
  -o GraphX/title_intro.c -n title_intro --header \
  --emit-u8-tiles --black-is-transparent --no-dedupe
```

### Dual-layer explicite (SCR1 + SCR2)

```bash
python tools/ngpc_tilemap.py scr1.png --scr2 scr2.png \
  -o GraphX/level1.c -n level1 --header --emit-u8-tiles
```

**Notes importantes :**
- `--emit-u8-tiles` : tiles en u8 (poids moitié en RAM, NGP_FAR toujours requis)
- `tiles_count` = nombre de mots u16 (= nb_tiles × 8), **pas** le nombre de tiles
- `map_tiles[]` = indices 0..N dans le set unique (ajouter TILE_BASE à l'affichage)
- `--no-dedupe` : désactive la déduplication (utile pour les écrans plein écran)

---

## 3. Méthode A — Helpers (méthode normale)

C'est la méthode recommandée. Elle nécessite que les helpers soient compilés
avec les signatures `NGP_FAR` correctes (template à jour).

```c
#include "ngpc_gfx.h"
#include "../GraphX/intro_ngpc_craft_png.h"

#define INTRO_TILE_BASE 128u  /* évite d'écraser la sysfont BIOS (tiles 32-127) */

static void intro_init(void)
{
    u16 i;

    ngpc_gfx_clear(GFX_SCR1);
    ngpc_gfx_clear(GFX_SCR2);
    ngpc_gfx_set_bg_color(RGB(0, 0, 0));

    /* Tiles — NGP_FAR géré en interne par le helper */
    ngpc_gfx_load_tiles_at(intro_ngpc_craft_png_tiles,
                           intro_ngpc_craft_png_tiles_count,
                           INTRO_TILE_BASE);

    /* Palettes */
    for (i = 0; i < (u16)intro_ngpc_craft_png_palette_count; ++i) {
        u16 off = (u16)i * 4u;
        ngpc_gfx_set_palette(GFX_SCR1, (u8)i,
            intro_ngpc_craft_png_palettes[off + 0],
            intro_ngpc_craft_png_palettes[off + 1],
            intro_ngpc_craft_png_palettes[off + 2],
            intro_ngpc_craft_png_palettes[off + 3]);
    }

    /* Map */
    for (i = 0; i < intro_ngpc_craft_png_map_len; ++i) {
        u8 x   = (u8)(i % intro_ngpc_craft_png_map_w);
        u8 y   = (u8)(i / intro_ngpc_craft_png_map_w);
        u16 tile = (u16)(INTRO_TILE_BASE + intro_ngpc_craft_png_map_tiles[i]);
        u8 pal = (u8)(intro_ngpc_craft_png_map_pals[i] & 0x0Fu);
        ngpc_gfx_put_tile(GFX_SCR1, x, y, tile, pal);
    }
}
```

---

## 4. Méthode B — VRAM brut / macros (solution de secours)

Utilise `src/gfx/ngpc_tilemap_blit.h`. Écrit directement en VRAM sans passer
de pointeurs en paramètre — évite totalement les problèmes near/far.

À utiliser quand :
- On suspecte un problème de pointeurs dans les helpers
- On veut une voie d'affichage 100% directe pour diagnostiquer

```c
#include "ngpc_tilemap_blit.h"
#include "../GraphX/intro_ngpc_craft_png.h"

#define INTRO_TILE_BASE 128u

static void intro_init(void)
{
    ngpc_gfx_clear(GFX_SCR1);
    ngpc_gfx_clear(GFX_SCR2);
    ngpc_gfx_set_bg_color(RGB(0, 0, 0));

    NGP_TILEMAP_BLIT_SCR1(intro_ngpc_craft_png, INTRO_TILE_BASE);
}
```

Ce que fait la macro :
1. Copie les tiles vers Character RAM (VRAM) à `0xA000` (16 bytes par tile)
2. Écrit la tilemap u16 directement dans `HW_SCR1_MAP` (0x9000)
3. Charge les palettes via `ngpc_gfx_set_palette()`

Fonctionne avec n'importe quel préfixe généré par `ngpc_tilemap.py` tant que
les symboles suivent le contrat (`prefix_tiles`, `prefix_map_tiles`,
`prefix_palettes`...).

---

## 5. Deux classes de bugs (rendu corrompu)

### Classe #1 — Init vidéo (registres)

Règle générale :
- Ne **jamais** écraser un registre vidéo entier avec `0` / `0xFF` si tous les
  bits ne sont pas connus.
- Préférer les opérations bitwise (`|=`, `&=`, `^=`) sur les bits documentés.

Exemple : `HW_SCR_PRIO` (0x8030) — le template force uniquement le bit 7
(priorité SCR1/SCR2) dans `src/core/ngpc_sys.c`.

### Classe #2 — cc900 near/far + assets en ROM

**Contexte :** la ROM est linkée à `0x200000`. Les assets `const` générées
vivent donc en `0x200000+`. cc900 a un modèle near/far : si un pointeur est
traité comme "near" (16 bits), l'adresse est tronquée → lecture au mauvais
endroit.

**Symptôme typique :** le converter sort des données correctes, mais le rendu
via certains helpers est "n'importe quoi" ou décalé.

**Fix :** les helpers du template utilisent `NGP_FAR` dans leurs signatures.
Voir [NGPC_CC900_GUIDE.md](NGPC_CC900_GUIDE.md) § Far pointers.

---

## 6. Checklist rapide — quand ça casse

1. **Palettes** : sont-elles chargées sur la bonne plane (SCR1 vs SCR2) ?
2. **Tile base** : as-tu évité d'écraser la sysfont (`tile_base >= 128`) ?
3. **Helpers** : es-tu sur un template qui définit `NGP_FAR` + signatures à jour ?
4. **Secours** : est-ce que `NGP_TILEMAP_BLIT_SCR1/_SCR2` rend OK ?
   - Si oui → l'asset est sain, le problème est dans les helpers (near/far)
   - Si non → l'asset est peut-être corrompu ou l'init vidéo est incorrecte
5. **Données brutes** : vérifier les tiles/map/palettes générées byte-à-byte
   avant d'accuser le pipeline C

---

## 7. Contraintes tilemap

| Contrainte | Valeur |
|---|---|
| Carte SCR | 32×32 tiles |
| Écran visible | 20×19 tiles (160×152 px) |
| Tiles disponibles | 128–511 (0–31 réservés, 32–127 = sysfont BIOS) |
| Palettes SCR | 16 palettes × 4 couleurs, format `0x0BGR` |
| Palette 0 couleur 0 | Transparente pour les scroll planes |
| Tiles max ROM | 512 tiles total (Character RAM = 8 KB) |
