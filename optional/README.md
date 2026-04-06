# Modules optionnels NGPC

Modules **à la carte** — ne font pas partie du template de base.
Copie uniquement ce dont tu as besoin dans `src/` pour ne pas alourdir la RAM, la compilation ni le dossier projet.

---

## Comment utiliser un module

1. **Copier** le sous-dossier dans `src/` de ton projet
   ```
   optional/ngpc_aabb/  →  src/ngpc_aabb/
   ```

2. **Ajouter** les `.rel` au makefile (pas pour les header-only) :
   ```makefile
   OBJS += src/ngpc_aabb/ngpc_aabb.rel
   OBJS += src/ngpc_tilecol/ngpc_tilecol.rel
   OBJS += src/ngpc_camera/ngpc_camera.rel
   # ngpc_fixed : rien à ajouter (header-only)
   ```

3. **Inclure** dans ton code :
   ```c
   #include "ngpc_fixed/ngpc_fixed.h"   /* header-only, toujours dispo */
   #include "ngpc_aabb/ngpc_aabb.h"
   #include "ngpc_tilecol/ngpc_tilecol.h"
   #include "ngpc_camera/ngpc_camera.h"
   ```

**Dépendances inter-modules :**
- `ngpc_aabb` inclut `ngpc_fixed` (pour le swept test)
- `ngpc_tilecol` inclut `ngpc_aabb` (pour les flags COL_*)
- `ngpc_camera` inclut `ngpc_gfx` (déjà dans le template de base)

Les modules s'appuient sur `ngpc_hw.h` (types u8/s16/etc.) accessible via `-Isrc/core` (déjà dans le makefile du template).

---

## Modules disponibles

### `ngpc_fixed` — Math fixe-point 8.4
**Type :** header-only · **RAM :** 0 octet · **Makefile :** rien à ajouter

Math entière subpixel pour positions et vélocités. Indispensable dès qu'on a de la physique ou du mouvement lisse.

| Élément | Description |
|---|---|
| `fx16` | Type fixe-point s16 (4 bits fractionnels, précision 1/16 px) |
| `FxVec2` | Paire `{ fx16 x, y }` pour position/vélocité 2D |
| `INT_TO_FX(x)` | Entier → fx16 |
| `FX_TO_INT(x)` | fx16 → entier (tronqué) |
| `FX_ROUND(x)` | fx16 → entier (arrondi) |
| `FX_LIT(f)` | Constante flottante compile-time (ex: `FX_LIT(0.25)`) |
| `FX_ADD/SUB/MUL/DIV` | Arithmétique fixe-point |
| `FX_SCALE(i, f)` | Entier × facteur fx16 → entier |
| `FX_LERP(a, b, t)` | Interpolation linéaire |
| `FX_CLAMP/MIN/MAX` | Utilitaires |
| `FX_SIGN(a)` | Signe en fx16 (-FX_ONE, 0, +FX_ONE) |

```c
/* Exemple physique platformer */
#define GRAVITY        FX_LIT(0.25)
#define MAX_FALL       INT_TO_FX(4)
#define JUMP_VEL       FX_LIT(-3.5)

FxVec2 pos = { INT_TO_FX(80), INT_TO_FX(60) };
FxVec2 vel = FXVEC2_ZERO;

/* Chaque frame : */
vel.y = FX_MIN(FX_ADD(vel.y, GRAVITY), MAX_FALL);
pos   = FXVEC2_ADD(pos, vel);
sprite_x = FX_TO_INT(pos.x);
sprite_y = FX_TO_INT(pos.y);
```

---

### `ngpc_aabb` — Collision rectangles
**Type :** .h + .c · **RAM :** 0 octet · **Dépend de :** ngpc_fixed

Collision rectangles axis-aligned. Fonctions pures, zéro état global.

| Fonction | Description |
|---|---|
| `ngpc_rect_overlap(a, b)` | 1 si les deux rects se chevauchent |
| `ngpc_rect_contains(r, px, py)` | 1 si le point est dans le rect |
| `ngpc_rect_test(a, b, *out)` | Overlap + côtés touchés + push MTV |
| `ngpc_rect_test_many(moving, list, n, *rx, *ry, *sides)` | Un mobile vs N statiques |
| `ngpc_swept_aabb(a, vx, vy, b, *out)` | Swept test pour projectiles rapides |
| `ngpc_rect_push_x/y(a, b)` | Pénétration sur un axe uniquement |
| `ngpc_rect_intersect(a, b, *out)` | Rectangle d'intersection |
| `ngpc_rect_offset(r, dx, dy)` | Déplacement du rect |

**Flags COL_\* :** `COL_LEFT`, `COL_RIGHT`, `COL_TOP`, `COL_BOTTOM`, `COL_ANY`

```c
/* Exemple joueur vs liste de plateformes */
NgpcCollResult cr;
if (ngpc_rect_test(&player_rect, &platform_rect, &cr)) {
    player.x += cr.push_x;
    player.y += cr.push_y;
    if (cr.hit & COL_BOTTOM) on_ground = 1;
    if (cr.hit & COL_TOP)    vel_y = 0;
}

/* Exemple balle rapide (swept) */
NgpcSweptResult sr;
ngpc_swept_aabb(&bullet_rect, bullet_vx, bullet_vy, &enemy_rect, &sr);
if (sr.hit) {
    /* sr.t  = moment exact [0..FX_ONE] */
    /* sr.nx / sr.ny = normale de collision */
    enemy_hp--;
}
```

---

### `ngpc_tilecol` — Collision tilemap
**Type :** .h + .c · **RAM :** 0 octet (+ la map de collision du jeu) · **Dépend de :** ngpc_aabb

Collision contre une map typée. **Contient `ngpc_tilecol_move()`, la fonction centrale de tout jeu d'action.**

**Types de tiles :**

| Constante | Valeur | Comportement |
|---|---|---|
| `TILE_PASS` | 0 | Passable, aucune collision |
| `TILE_SOLID` | 1 | Solide sur tous les côtés |
| `TILE_ONE_WAY` | 2 | Plateforme traversable — solide seulement par le haut |
| `TILE_DAMAGE` | 3 | Passable, signalé dans `result.in_damage` |
| `TILE_LADDER` | 4 | Zone d'échelle, signalé dans `result.in_ladder` |
| 5-15 | — | Libres pour usage projet |

**Coût RAM de la map :** `map_w × map_h` octets
- Écran plein : 20×19 = **380 octets**
- Map maximale : 32×32 = **1024 octets** (attention au budget 12 KB)

| Fonction | Description |
|---|---|
| `ngpc_tilecol_move(col, *rx, *ry, w, h, dx, dy, *res)` | **Déplace + résout** la collision, remplit NgpcMoveResult |
| `ngpc_tilecol_on_ground(col, rx, ry, w, h)` | 1 si posé sur un sol (solid ou one-way) |
| `ngpc_tilecol_on_ceiling(col, rx, ry, w, h)` | 1 si tête dans un plafond |
| `ngpc_tilecol_on_wall_left/right(...)` | 1 si contre un mur |
| `ngpc_tilecol_ground_dist(col, rx, ry, w, h, max)` | Distance jusqu'au sol |
| `ngpc_tilecol_rect_solid(col, wx, wy, w, h)` | Test brut zone vs tiles solides |
| `ngpc_tilecol_type_at(col, wx, wy)` | Type du tile à une position pixel |

**`NgpcMoveResult` après `ngpc_tilecol_move()` :**
```c
res.sides     /* COL_* : quels côtés ont heurté */
res.tile_x    /* type du tile bloquant en X */
res.tile_y    /* type du tile bloquant en Y */
res.in_ladder /* 1 si dans une zone TILE_LADDER */
res.in_damage /* 1 si dans une zone TILE_DAMAGE */
```

> **Contrainte :** `|dx|` et `|dy|` ≤ 8 pixels/frame pour éviter le tunnel-through.
> À 60fps, 8px/frame = 480px/s. Largement suffisant pour un jeu NGPC.

```c
/* Exemple platformer complet */
static const u8 s_map[MAP_W * MAP_H] = {
    1,1,1,1,1,1,1,1,
    1,0,0,0,0,0,0,1,
    1,0,0,2,2,0,0,1,   /* 2 = one-way platform */
    1,0,0,0,0,0,0,1,
    1,1,1,1,1,1,1,1,
};
NgpcTileCol col = { s_map, MAP_W, MAP_H };

/* Chaque frame : */
vel.y = FX_MIN(FX_ADD(vel.y, GRAVITY), MAX_FALL);
s16 dx = FX_TO_INT(vel.x);
s16 dy = FX_TO_INT(vel.y);

NgpcMoveResult res;
ngpc_tilecol_move(&col, &px, &py, PW, PH, dx, dy, &res);

if (res.sides & COL_BOTTOM) { on_ground = 1; vel.y = 0; }
if (res.sides & COL_TOP)    { vel.y = 0; }
if (res.sides & (COL_LEFT | COL_RIGHT)) { vel.x = 0; }
if (res.in_damage) { player_hurt(); }
if (res.in_ladder) { can_climb = 1; }
```

---

### `ngpc_camera` — Caméra
**Type :** .h + .c · **RAM :** ~10 octets par caméra · **Dépend de :** ngpc_gfx (template de base)

| Fonction | Description |
|---|---|
| `ngpc_cam_init(cam, level_w, level_h, flags)` | Initialise (CAM_FLAG_CLAMP pour bornes de niveau) |
| `ngpc_cam_follow(cam, tx, ty)` | Centre instantanément sur la cible |
| `ngpc_cam_follow_smooth(cam, tx, ty, speed)` | Suivi progressif (speed 1=lent .. 8=rapide) |
| `ngpc_cam_apply(cam, plane)` | Applique le scroll sur GFX_SCR1 / GFX_SCR2 |
| `ngpc_cam_world_to_screen(cam, wx, wy, *sx, *sy)` | Coords monde → coords écran (pour placer sprites) |
| `ngpc_cam_on_screen(cam, wx, wy, margin)` | 1 si visible (+ marge) — culling basique |

```c
NgpcCamera cam;
ngpc_cam_init(&cam, LEVEL_W * 8, LEVEL_H * 8, CAM_FLAG_CLAMP);

/* Chaque frame : */
ngpc_cam_follow_smooth(&cam, player_x, player_y, 4);
ngpc_cam_apply(&cam, GFX_SCR1);

/* Placer le sprite du joueur en coords écran : */
s16 sx, sy;
ngpc_cam_world_to_screen(&cam, player_x, player_y, &sx, &sy);
ngpc_sprite_move(0, sx, sy);
```

---

## `ngpc_timer` — Timers de jeu
**Type :** .h + .c · **RAM :** 3 octets/timer · **Makefile :** `OBJS += src/ngpc_timer/ngpc_timer.rel`

Countdown, cooldown, tick périodique. One-shot ou répétitif. Appeler `ngpc_timer_update()` une fois par frame.

| Fonction / Macro | Description |
|---|---|
| `ngpc_timer_start(t, frames)` | Démarre un timer one-shot de N frames |
| `ngpc_timer_start_repeat(t, period)` | Démarre un timer répétitif (relance auto) |
| `ngpc_timer_stop(t)` | Stoppe sans réinitialiser |
| `ngpc_timer_restart(t)` | Repart depuis 0 avec la durée mémorisée |
| `ngpc_timer_update(t)` | Met à jour — retourne 1 si expiré ce frame |
| `ngpc_timer_active(t)` | 1 si le timer compte |
| `ngpc_timer_done(t)` | 1 si one-shot expiré (vrai 1 seul frame) |
| `ngpc_timer_remaining(t)` | Frames restantes |

```c
/* Cooldown d'attaque */
NgpcTimer atk_cd;
ngpc_timer_start(&atk_cd, 20);          /* 20 frames de cooldown */

/* Chaque frame : */
ngpc_timer_update(&atk_cd);
if (!ngpc_timer_active(&atk_cd)) { /* peut attaquer */ }

/* Timer répétitif (spawn ennemi toutes les 3 secondes = 180 frames) */
NgpcTimer spawn_t;
ngpc_timer_start_repeat(&spawn_t, 180);
if (ngpc_timer_update(&spawn_t)) { spawn_enemy(); }
```

---

## `ngpc_anim` — Animation de sprites
**Type :** .h + .c · **RAM :** 4 octets/NgpcAnim · **Makefile :** `OBJS += src/ngpc_anim/ngpc_anim.rel`

Séquence de frames avec vitesse configurable. Modes : LOOP, PINGPONG, ONESHOT.
`NgpcAnimDef` est const (en ROM), `NgpcAnim` est l'état courant (en RAM).

| Élément | Description |
|---|---|
| `NgpcAnimDef` | Définition const (frames[], count, speed, flags) |
| `NgpcAnim` | État courant : frame, tick, done |
| `ANIM_DEF(frm, cnt, spd, flg)` | Macro de déclaration en ROM |
| `ANIM_LOOP` / `ANIM_PINGPONG` / `ANIM_ONESHOT` | Modes de lecture |
| `ngpc_anim_play(a, def)` | Lance une animation (no-op si déjà en cours) |
| `ngpc_anim_restart(a)` | Force le redémarrage depuis frame 0 |
| `ngpc_anim_update(a)` | Avance l'anim — retourne 1 si frame changée |
| `ngpc_anim_tile(a)` | Index tile courant (à ajouter à TILE_BASE) |
| `ngpc_anim_done(a)` | 1 si ONESHOT terminé |

```c
static const u8 run_f[] = { 2, 3, 4, 5 };
static const u8 idle_f[] = { 0, 1 };
static const NgpcAnimDef anim_run  = ANIM_DEF(run_f,  4, 4, ANIM_LOOP);
static const NgpcAnimDef anim_idle = ANIM_DEF(idle_f, 2, 8, ANIM_LOOP);

NgpcAnim anim;
ngpc_anim_play(&anim, &anim_idle);

/* Chaque frame : */
ngpc_anim_update(&anim);
ngpc_sprite_set(0, px, py, TILE_BASE + ngpc_anim_tile(&anim), pal, 0);

/* Changer d'animation selon l'état : */
if (moving) ngpc_anim_play(&anim, &anim_run);
else        ngpc_anim_play(&anim, &anim_idle);
```

---

## `ngpc_fsm` — Machine d'états
**Type :** header-only · **RAM :** 3 octets/NgpcFsm · **Makefile :** rien

Suivi des transitions d'état. `ngpc_fsm_entered()` est vrai exactement 1 frame après chaque transition — idéal pour les initialisations d'état.

| Macro | Description |
|---|---|
| `ngpc_fsm_init(f, initial)` | Initialise dans l'état `initial` |
| `ngpc_fsm_goto(f, state)` | Transition vers un nouvel état |
| `ngpc_fsm_entered(f)` | 1 le premier frame d'un état (init) |
| `ngpc_fsm_changed(f)` | 1 si l'état a changé ce frame |
| `ngpc_fsm_tick(f)` | À appeler en FIN de frame (efface les flags) |

```c
#define ST_IDLE 0
#define ST_RUN  1
#define ST_HIT  2

NgpcFsm fsm;
ngpc_fsm_init(&fsm, ST_IDLE);

/* Chaque frame : */
switch (fsm.cur) {
    case ST_IDLE:
        if (ngpc_fsm_entered(&fsm)) { ngpc_anim_play(&anim, &anim_idle); }
        if (ngpc_pad_pressed & PAD_RIGHT) ngpc_fsm_goto(&fsm, ST_RUN);
        break;
    case ST_RUN:
        if (ngpc_fsm_entered(&fsm)) { ngpc_anim_play(&anim, &anim_run); }
        if (!(ngpc_pad_held & PAD_RIGHT)) ngpc_fsm_goto(&fsm, ST_IDLE);
        break;
}
ngpc_fsm_tick(&fsm);   /* toujours en dernier */
```

---

## `ngpc_pool` — Pool d'objets
**Type :** .h + .c · **RAM :** 3 octets/pool + taille des objets · **Makefile :** `OBJS += src/ngpc_pool/ngpc_pool.rel`

Allocation/libération O(1) sans malloc. Bitmask u16 → max 16 slots. Utiliser `NGPC_POOL_DECL` pour créer un pool typé.

| Élément | Description |
|---|---|
| `NgpcPoolHdr` | En-tête : mask, count, capacity |
| `NGPC_POOL_DECL(Name, Type, N)` | Déclare un pool typé de N objets de type Type |
| `NGPC_POOL_INIT(pool_ptr, N)` | Initialise avant utilisation |
| `ngpc_pool_alloc(hdr)` | Alloue un slot — retourne index ou `POOL_NONE` |
| `ngpc_pool_free(hdr, idx)` | Libère le slot idx |
| `ngpc_pool_clear(hdr)` | Vide tout le pool |
| `ngpc_pool_active(hdr, idx)` | 1 si le slot est occupé |
| `ngpc_pool_count(hdr)` | Nombre de slots occupés |
| `POOL_EACH(hdr, i)` | Itère sur les slots actifs uniquement |
| `POOL_NONE` | Index invalide (0xFF) |

```c
typedef struct { s16 x, y; s8 vx, vy; } Bullet;
NGPC_POOL_DECL(BulletPool, Bullet, 8);
static BulletPool bullets;
NGPC_POOL_INIT(&bullets, 8);

/* Spawn : */
u8 idx = ngpc_pool_alloc(&bullets.hdr);
if (idx != POOL_NONE) {
    bullets.items[idx].x = player_x;
    bullets.items[idx].vx = 3;
}

/* Update all active : */
POOL_EACH(&bullets.hdr, i) {
    bullets.items[i].x += bullets.items[i].vx;
    if (out_of_bounds) ngpc_pool_free(&bullets.hdr, i);
}
```

---

## `ngpc_menu` — Menu de sélection
**Type :** .h + .c · **RAM :** 6 octets · **Makefile :** `OBJS += src/ngpc_menu/ngpc_menu.rel`

Navigation D-pad + validation PAD_A. Affichage sur tilemap.
**Dépend de :** `ngpc_input.h` (core) et `ngpc_text.h` (gfx).

| Fonction | Description |
|---|---|
| `ngpc_menu_init(m, items, count, wrap)` | Initialise avec un tableau de chaînes |
| `ngpc_menu_update(m)` | Lit l'input — retourne index si A pressé, `MENU_NONE` sinon |
| `ngpc_menu_draw(m, plane, tx, ty, ch)` | Dessine le menu (cursor_char = '>' par ex.) |
| `ngpc_menu_erase(m, plane, tx, ty, w)` | Efface la zone du menu |
| `m->changed` | 1 si le curseur a bougé ce frame (pour redraw conditionnel) |
| `MENU_NONE` | Valeur retournée si aucune sélection (0xFF) |

```c
static const char *labels[] = { "JOUER", "OPTIONS", "QUITTER" };
static NgpcMenu menu;
ngpc_menu_init(&menu, labels, 3, 1);    /* wrap=1 */
ngpc_menu_draw(&menu, PLANE_SCR1, 7, 6, '>');

/* Chaque frame : */
u8 sel = ngpc_menu_update(&menu);
if (menu.changed) ngpc_menu_draw(&menu, PLANE_SCR1, 7, 6, '>');
if (sel != MENU_NONE) {
    switch (sel) {
        case 0: start_game(); break;
        case 1: open_options(); break;
        case 2: ngpc_shutdown(); break;
    }
}
```

---

## `ngpc_easing` — Fonctions de lissage
**Type :** header-only · **RAM :** 0 octet · **Makefile :** rien · **Dépend de :** ngpc_fixed

Easing en fixe-point 8.4. Toutes les fonctions prennent `t ∈ [0..FX_ONE]` et retournent `[0..FX_ONE]`.

| Macro | Description |
|---|---|
| `EASE_LINEAR(t)` | Identité |
| `EASE_IN_QUAD(t)` / `EASE_OUT_QUAD(t)` / `EASE_INOUT_QUAD(t)` | Quadratique |
| `EASE_IN_CUBIC(t)` / `EASE_OUT_CUBIC(t)` / `EASE_INOUT_CUBIC(t)` | Cubique |
| `EASE_SMOOTH(t)` | Hermite 3t²-2t³ (dérivée nulle aux extrêmes) |
| `EASE_LERP(a, b, tick, total, fn)` | Interpolation lissée d'un compteur de frames |

```c
/* Déplacer la caméra avec ease-out en 30 frames */
fx16 x = EASE_LERP(INT_TO_FX(0), INT_TO_FX(100), frame, 30, EASE_OUT_QUAD);
```

---

## `ngpc_platform` — Physique platformer
**Type :** .h + .c · **RAM :** 11 octets · **Makefile :** `OBJS += src/ngpc_platform/ngpc_platform.rel` · **Dépend de :** ngpc_fixed

Gravité, saut variable, coyote time (6 frames), jump buffer (8 frames). La collision reste dans le code jeu.

| Élément | Description |
|---|---|
| `ngpc_platform_init(p, x, y)` | Initialise au repos |
| `ngpc_platform_update(p)` | Gravité + intégration pos (avant collision) |
| `ngpc_platform_land(p)` | Appeler quand le sol est détecté — exécute saut bufferisé si présent |
| `ngpc_platform_press_jump(p)` | Pression saut : immédiat ou stocké en buffer |
| `ngpc_platform_release_jump(p)` | Relâchement : variable jump height |
| `ngpc_platform_on_ground(p)` | 1 si posé |
| `ngpc_platform_px/py(p)` | Position pixel |

Constantes `#define`-surchargeables : `PLAT_GRAVITY` `PLAT_MAX_FALL` `PLAT_JUMP_VEL` `PLAT_COYOTE_FRAMES` `PLAT_JUMP_BUF_FRAMES`

```c
NgpcPlatform p;
ngpc_platform_init(&p, INT_TO_FX(80), INT_TO_FX(60));
/* Chaque frame : */
ngpc_platform_update(&p);
resolve_collisions(&p);    /* code jeu : ajuste p.pos.y + appelle ngpc_platform_land() */
if (ngpc_pad_pressed & PAD_A)  ngpc_platform_press_jump(&p);
if (ngpc_pad_released & PAD_A) ngpc_platform_release_jump(&p);
```

---

## `ngpc_actor` — Mouvement top-down
**Type :** .h + .c · **RAM :** 17 octets · **Makefile :** `OBJS += src/ngpc_actor/ngpc_actor.rel` · **Dépend de :** ngpc_fixed

Déplacement 4/8 directions, accélération, vitesse max, friction. Normalisation des diagonales.

| Élément | Description |
|---|---|
| `ngpc_actor_init(a, x, y, speed, accel, friction)` | Initialise |
| `ngpc_actor_move(a, dx, dy)` | Direction ce frame (dx,dy ∈ {-1,0,+1}) — appeler AVANT update |
| `ngpc_actor_update(a)` | Friction si immobile, intègre pos |
| `ngpc_actor_stop(a)` | Stoppe instantanément |
| `a->dir_x` / `a->dir_y` | Dernière direction (pour flip sprite ou animation) |
| `ACTOR_4DIR_H/V(dx,dy)` | Helpers priorité horizontal en mode 4 directions |

```c
NgpcActor hero;
ngpc_actor_init(&hero, INT_TO_FX(80), INT_TO_FX(76),
                ACTOR_DEFAULT_SPEED, ACTOR_DEFAULT_ACCEL, ACTOR_DEFAULT_FRICTION);
/* Chaque frame : */
s8 dx = (ngpc_pad_held & PAD_RIGHT) ? 1 : (ngpc_pad_held & PAD_LEFT) ? -1 : 0;
s8 dy = (ngpc_pad_held & PAD_DOWN)  ? 1 : (ngpc_pad_held & PAD_UP)   ? -1 : 0;
ngpc_actor_move(&hero, dx, dy);
ngpc_actor_update(&hero);
ngpc_sprite_set(0, ngpc_actor_px(&hero), ngpc_actor_py(&hero),
                tile, pal, hero.dir_x < 0 ? SPR_HFLIP : 0);
```

---

## `ngpc_particle` — Pool de particules
**Type :** .h + .c · **RAM :** `PARTICLE_POOL_SIZE × 12` octets (défaut : 192) · **Makefile :** `OBJS += src/ngpc_particle/ngpc_particle.rel` · **Dépend de :** ngpc_fixed

Pool statique avec durée de vie, vélocité et gravité optionnelle. Le rendu est à la charge du jeu.

| Élément | Description |
|---|---|
| `ngpc_particle_emit(pool, x, y, vx, vy, life, tile, pal, flags)` | Émet une particule |
| `ngpc_particle_burst(pool, x, y, count, speed, ...)` | Explose en étoile (8 directions, boucle si count>8) |
| `ngpc_particle_update(pool)` | Physique + décrément life (appeler une fois par frame) |
| `PART_GRAVITY` | Flag : appliquer PARTICLE_GRAVITY à vel.y |
| `ngpc_particle_px/py(p)` | Position pixel entière |

```c
static NgpcParticlePool fx;
ngpc_particle_pool_init(&fx);
/* À l'impact : */
ngpc_particle_burst(&fx, pos_x, pos_y, 8, INT_TO_FX(1), 20, SPARK_TILE, 2, PART_GRAVITY);
/* Chaque frame : */
ngpc_particle_update(&fx);
for (i = 0; i < PARTICLE_POOL_SIZE; i++) {
    NgpcParticle *p = &fx.slots[i];
    if (!p->life) { ngpc_sprite_hide(SPR_FX + i); continue; }
    ngpc_sprite_set(SPR_FX + i, ngpc_particle_px(p), ngpc_particle_py(p),
                    p->tile, p->pal, SPR_FRONT);
}
```

---

## `ngpc_tween` — Interpolation dans le temps
**Type :** .h + .c · **RAM :** 10 octets · **Makefile :** `OBJS += src/ngpc_tween/ngpc_tween.rel` · **Dépend de :** ngpc_easing (→ ngpc_fixed)

Tweene une valeur `fx16` de `from` à `to` en N frames avec easing. Modes : one-shot, loop, pingpong.

| Élément | Description |
|---|---|
| `ngpc_tween_start(tw, from, to, duration, ease, flags)` | Lance le tween |
| `ngpc_tween_update(tw)` | Avance d'un frame — retourne 1 si en cours, 0 si terminé |
| `ngpc_tween_restart(tw)` | Repart depuis from sans changer les paramètres |
| `tw->value` | Valeur interpolée courante (à lire après update) |
| `ngpc_tween_is_done(tw)` | 1 si one-shot terminé |
| `TWEEN_LOOP` / `TWEEN_PINGPONG` | Flags de mode (passer dans flags) |
| `TWEEN_EASE_OUT_QUAD` … `TWEEN_EASE_SMOOTH` | Fonctions d'easing disponibles |

```c
/* Fondu de luminosité 0→8 en 30 frames */
NgpcTween fade;
ngpc_tween_start(&fade, INT_TO_FX(0), INT_TO_FX(8), 30, TWEEN_EASE_OUT_QUAD, 0);
/* Chaque frame : */
ngpc_tween_update(&fade);
ngpc_palfx_set_brightness(0, FX_TO_INT(fade.value));

/* Pulsation infinie avec PINGPONG + EASE_SMOOTH */
NgpcTween pulse;
ngpc_tween_start(&pulse, INT_TO_FX(0), INT_TO_FX(7), 45, TWEEN_EASE_SMOOTH, TWEEN_PINGPONG);
```

---

## `ngpc_bullet` — Pool de projectiles
**Type :** .h + .c · **RAM :** `BULLET_POOL_SIZE × 12` octets (défaut : 192) · **Makefile :** `OBJS += src/ngpc_bullet/ngpc_bullet.rel` · **Dépend de :** ngpc_pool, ngpc_fixed, ngpc_aabb

Pool de projectiles avec déplacement, expiration automatique (TTL + hors écran) et collision rect.

| Élément | Description |
|---|---|
| `NGPC_BULLET_POOL_INIT(pool)` | Initialise le pool |
| `ngpc_bullet_spawn(pool, x, y, vx, vy, w, h, tile, pal, life, flags)` | Spawne un bullet (retourne l'index ou POOL_NONE) |
| `ngpc_bullet_update(pool)` | Déplace + expire bullets (OOB ou TTL) — une fois par frame |
| `ngpc_bullet_hits(pool, idx, target_rect)` | Test de collision bullet vs rect |
| `ngpc_bullet_kill(pool, idx)` | Libère un bullet après collision |
| `ngpc_bullet_px/py(b)` | Position pixel pour ngpc_sprite_set |
| `BULLET_PLAYER` / `BULLET_ENEMY` | Flags pour discriminer les factions |

`life = 0` → le bullet ne s'expire que hors écran.

```c
static NgpcBulletPool bullets;
NGPC_BULLET_POOL_INIT(&bullets);

/* Tir : */
ngpc_bullet_spawn(&bullets, hero.pos.x, hero.pos.y,
                  4, 0, 4, 4, BULLET_TILE, 1, 60, BULLET_PLAYER);

/* Chaque frame : */
ngpc_bullet_update(&bullets);
POOL_EACH(&bullets.hdr, i) {
    NgpcBullet *b = &bullets.items[i];
    /* Rendu : */
    ngpc_sprite_set(SPR_BULLET + i, ngpc_bullet_px(b), ngpc_bullet_py(b),
                    b->tile, b->pal, SPR_FRONT);
    /* Collision ennemi : */
    NgpcRect er = { ex, ey, 16, 16 };
    if ((b->flags & BULLET_PLAYER) && ngpc_bullet_hits(&bullets, i, &er)) {
        enemy_hurt();
        ngpc_bullet_kill(&bullets, i);
    }
}
```

---

---

## `ngpc_kinematic` — Corps physique générique
**Type :** .h + .c · **RAM :** 11 octets · **Makefile :** `OBJS += src/ngpc_kinematic/ngpc_kinematic.rel` · **Dépend de :** ngpc_fixed, ngpc_tilecol

Corps générique avec vélocité fx16, friction multiplicative et rebond. Intègre `ngpc_tilecol_move()` — pour rochers, barils, balles, ennemis à physique simple.

| Élément | Description |
|---|---|
| `ngpc_kinematic_init(k, x, y, friction, bounce)` | Initialise |
| `ngpc_kinematic_apply_gravity(k, gravity, max_fall)` | Ajoute la gravité à vel.y |
| `ngpc_kinematic_move(k, col, w, h)` | Friction → intégration → collision → rebond |
| `ngpc_kinematic_impulse(k, ix, iy)` | Impulsion instantanée |
| `KIN_FRICTION_NONE/LOW/MEDIUM/HIGH` | Presets ×1.0 / ×0.94 / ×0.875 / ×0.75 |
| `KIN_BOUNCE_NONE/SOFT/ELASTIC/PERFECT` | Presets 0 / ×0.5 / ×0.81 / ×1.0 |

```c
NgpcKinematic rock;
ngpc_kinematic_init(&rock, INT_TO_FX(80), INT_TO_FX(10),
                    KIN_FRICTION_MEDIUM, KIN_BOUNCE_ELASTIC);
/* Chaque frame : */
ngpc_kinematic_apply_gravity(&rock, KIN_GRAVITY, KIN_MAX_FALL);
ngpc_kinematic_move(&rock, &col, 8, 8);
ngpc_sprite_set(SPR_ROCK, ngpc_kinematic_px(&rock), ngpc_kinematic_py(&rock),
                ROCK_TILE, 0, 0);
```

---

## `ngpc_hud` — Éléments HUD
**Type :** .h + .c · **RAM :** 9 octets/barre · **Makefile :** `OBJS += src/ngpc_hud/ngpc_hud.rel` · **Dépend de :** ngpc_gfx, ngpc_text, ngpc_sprite (core)

Barre de valeur (HP/énergie), score et compteur de vies précâblés.

| Élément | Description |
|---|---|
| `ngpc_hud_bar_init(bar, plane, tx, ty, len, max, tf, th, te, pal)` | Initialise une barre |
| `ngpc_hud_bar_set(bar, value)` | Change valeur + redessine |
| `ngpc_hud_score_draw(plane, pal, tx, ty, score, digits, zero_pad)` | Affiche un score |
| `ngpc_hud_lives_draw(spr_base, x, y, lives, max, tile, pal, spacing)` | Icônes vies |

`tile_half = 0` → précision simple (1 unité/tile). Sinon double précision (2 unités/tile).

```c
static NgpcHudBar hp;
ngpc_hud_bar_init(&hp, GFX_SCR1, 1, 0, 4, 8,
                  TILE_HP_FULL, TILE_HP_HALF, TILE_HP_EMPTY, 0);
ngpc_hud_bar_set(&hp, player_hp);
ngpc_hud_score_draw(GFX_SCR1, 0, 13, 0, score, 6, 0);
ngpc_hud_lives_draw(SPR_LIVES, 2, 1, lives, 4, LIFE_TILE, 0, 10);
```

---

## `ngpc_dialog` — Boîte de dialogue
**Type :** .h + .c · **RAM :** 14 octets · **Makefile :** `OBJS += src/ngpc_dialog/ngpc_dialog.rel` · **Dépend de :** ngpc_gfx, ngpc_text, ngpc_input (core)

Texte lettre par lettre, indicateur `▶` clignotant, jusqu'à 2 choix D-pad.

| Élément | Description |
|---|---|
| `ngpc_dialog_open(d, plane, bx, by, bw, bh, pal)` | Ouvre et dessine le cadre |
| `ngpc_dialog_set_text(d, text)` | Texte courant (supporte `\n`) |
| `ngpc_dialog_set_choices(d, choices, count)` | Ajoute des choix (max 2) |
| `ngpc_dialog_update(d)` | `DIALOG_RUNNING / DONE / CHOICE_0 / CHOICE_1` |
| `ngpc_dialog_is_open(d)` | 1 si en cours (bloquer gameplay) |
| `DIALOG_TEXT_SPEED` | Frames/lettre (défaut 2, surchargeable) |

```c
static NgpcDialog dlg;
ngpc_dialog_open(&dlg, GFX_SCR1, 0, 16, 20, 3, 0);
ngpc_dialog_set_text(&dlg, "Bonjour !\nAppuie sur A pour continuer.");
/* Chaque frame (si dialogue actif) : */
u8 r = ngpc_dialog_update(&dlg);
if (r == DIALOG_DONE) game_resume();
```

---

## `ngpc_entity` — Système d'entités
**Type :** .h + .c · **RAM :** `ENTITY_COUNT × (8 + ENTITY_DATA_SIZE)` octets · **Makefile :** `OBJS += src/ngpc_entity/ngpc_entity.rel` · **Dépend de :** rien

Tableau statique avec flag active/inactive. Dispatch par `switch(type)` dans `entity_update()` / `entity_draw()` fournies par le jeu — pas de pointeurs de fonction.

| Élément | Description |
|---|---|
| `ENTITY_COUNT` | Taille du pool (défaut 8) |
| `ENTITY_DATA_SIZE` | Octets de données jeu par entité (défaut 8) |
| `ngpc_entity_spawn(type, x, y)` | Alloue un slot (retourne pointeur ou NULL) |
| `ngpc_entity_kill(e)` | Macro — désactive |
| `ngpc_entity_update_all()` | Appelle `entity_update(e)` sur chaque active |
| `ngpc_entity_draw_all()` | Appelle `entity_draw(e)` sur chaque active |
| `ngpc_entity_find(type)` | Premier slot actif de ce type |

Le jeu **doit** implémenter `void entity_update(NgpcEntity *e)` et `void entity_draw(const NgpcEntity *e)`.

```c
void entity_update(NgpcEntity *e) {
    switch (e->type) {
        case ENT_SLIME: slime_update(e); break;
        case ENT_COIN:  if (--e->timer == 0) ngpc_entity_kill(e); break;
    }
}
/* Init niveau : */
ngpc_entity_init_all();
NgpcEntity *s = ngpc_entity_spawn(ENT_SLIME, 64, 40);
s->data[0] = 3;  /* HP */
/* Chaque frame : */
ngpc_entity_update_all();
ngpc_entity_draw_all();
```

---

## `ngpc_room` — Transitions entre rooms
**Type :** .h + .c · **RAM :** 4 octets · **Makefile :** `OBJS += src/ngpc_room/ngpc_room.rel` · **Dépend de :** rien

Timer qui séquence fade-out → chargement → fade-in. Gère uniquement le timing ; l'effet visuel est à la charge du jeu (ngpc_palfx recommandé).

| Élément | Description |
|---|---|
| `ngpc_room_init(r, phase_frames)` | Initialise (ex: 30 frames/phase) |
| `ngpc_room_go(r, next_room)` | Démarre la transition |
| `ngpc_room_loaded(r)` | Signale que le chargement est terminé → fade-in |
| `ngpc_room_update(r)` | `ROOM_IDLE / FADE_OUT / LOAD / FADE_IN / DONE` |
| `ngpc_room_in_transition(r)` | 1 si en cours |
| `ngpc_room_progress(r)` | Progression [0..255] de la phase courante |

```c
static NgpcRoom room;
ngpc_room_init(&room, 30);
/* Déclencher : */
ngpc_palfx_fade_to_black(GFX_SCR1, 0, 2);
ngpc_room_go(&room, ROOM_CAVE);
/* Chaque frame : */
u8 r = ngpc_room_update(&room);
if (r == ROOM_LOAD) {
    load_level(room.next_room);
    ngpc_gfx_set_palette(GFX_SCR1, 0, 0, 0, 0, 0);
    ngpc_palfx_fade(GFX_SCR1, 0, level_pal, 2);
    ngpc_room_loaded(&room);
}
if (r == ROOM_DONE) gameplay_active = 1;
```

---

## `ngpc_grid` — Logique grille puzzle
**Type :** header-only · **RAM :** 0 (+ buffer jeu) · **Makefile :** rien · **Dépend de :** rien

Grille `u8[]` fournie par le jeu. Accès, conversion coords pixel↔tile, utilitaires match-3/Sokoban.

| Élément | Description |
|---|---|
| `ngpc_grid_init(g, cells, w, h)` | Associe un buffer |
| `ngpc_grid_get/set(g, tx, ty)` | Lecture/écriture |
| `ngpc_grid_at(g, tx, ty)` | Pointeur cellule (NULL si hors bornes) |
| `ngpc_grid_swap(g, ax, ay, bx, by)` | Échange deux cellules |
| `ngpc_grid_to_screen(g, tx, ty, ox, oy, cw, ch, *sx, *sy)` | Tile → pixel |
| `ngpc_grid_from_screen(g, px, py, ox, oy, cw, ch, *tx, *ty)` | Pixel → tile |
| `ngpc_grid_count_h/v(g, tx, ty, value)` | Cellules consécutives H/V |
| `ngpc_grid_find(g, value, *tx, *ty)` | Première cellule d'une valeur |

```c
static u8 cells[8 * 8];
static NgpcGrid grid;
ngpc_grid_init(&grid, cells, 8, 8);
ngpc_grid_fill(&grid, CELL_EMPTY);
/* Match-3 : */
if (ngpc_grid_count_h(&grid, x, y, CELL_RED) >= 3) clear_h(&grid, x, y);
/* Sokoban : */
u8 *dst = ngpc_grid_at(&grid, px + dx, py + dy);
if (dst && *dst == CELL_EMPTY) { *dst = CELL_PLAYER; ngpc_grid_set(&grid, px, py, CELL_EMPTY); }
```

---

## `ngpc_path` — Pathfinding BFS
**Type :** .h + .c · **RAM :** 320 octets statiques internes · **Makefile :** `OBJS += src/ngpc_path/ngpc_path.rel` · **Dépend de :** rien

BFS flood-fill inverse (depuis la cible) sur grille max 16×16. Retourne le premier pas ou la distance totale. Map compatible `NgpcTileCol` (0 = passable).

| Élément | Description |
|---|---|
| `ngpc_path_step(map, w, h, sx, sy, tx, ty, *dx, *dy)` | Premier pas vers la cible (retourne 1 si chemin trouvé) |
| `ngpc_path_dist(map, w, h, sx, sy, tx, ty)` | Distance (PATH_NO_PATH = 0xFF si inaccessible) |

```c
/* Ennemi suit le joueur : */
s8 dx, dy;
if (ngpc_path_step(col.map, MAP_W, MAP_H,
                   enemy_tx, enemy_ty, player_tx, player_ty, &dx, &dy)) {
    enemy_tx += dx; enemy_ty += dy;
}
/* IA conditionnelle : */
u8 d = ngpc_path_dist(col.map, MAP_W, MAP_H, etx, ety, ptx, pty);
if (d <= 2) attack(); else if (d != PATH_NO_PATH) chase(); else wander();
```

---

> Les modules suivants sont **déjà dans le core** et n'ont pas besoin d'un module optionnel :
> `ngpc_input` · `ngpc_text` · `ngpc_sprite` · `ngpc_math` (rand, sin, cos) · `ngpc_palfx` (fade, flash) · `ngpc_flash` (save 256 B)

---

## Modules par genre

| Genre | Modules recommandés |
|---|---|
| **Platformer** | `ngpc_platform` ✓, `ngpc_tilecol` ✓, `ngpc_anim` ✓, `ngpc_timer` ✓, `ngpc_pool` ✓, `ngpc_bullet` ✓, `ngpc_kinematic` ✓, `ngpc_room` ✓ |
| **Shooter** | `ngpc_bullet` ✓, `ngpc_pool` ✓, `ngpc_particle` ✓, `ngpc_anim` ✓, `ngpc_timer` ✓, `ngpc_aabb` ✓, `ngpc_hud` ✓ |
| **RPG / Aventure** | `ngpc_actor` ✓, `ngpc_menu` ✓, `ngpc_fsm` ✓, `ngpc_camera` ✓, `ngpc_anim` ✓, `ngpc_tween` ✓, `ngpc_dialog` ✓, `ngpc_room` ✓, `ngpc_entity` ✓, `ngpc_path` ✓ |
| **Puzzle** | `ngpc_menu` ✓, `ngpc_timer` ✓, `ngpc_tween` ✓, `ngpc_easing` ✓, `ngpc_fsm` ✓, `ngpc_grid` ✓ |
| **Action top-down** | `ngpc_actor` ✓, `ngpc_bullet` ✓, `ngpc_fsm` ✓, `ngpc_aabb` ✓, `ngpc_anim` ✓, `ngpc_particle` ✓, `ngpc_entity` ✓, `ngpc_path` ✓, `ngpc_hud` ✓ |
