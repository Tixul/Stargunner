/*
 * stage.c - Simple timeline stage scripting (deterministic spawns)
 *
 * Part of NGPC Template 2026 (MIT License)
 *
 * Nemesis/Gradius-style timing model:
 *   StageEvt::delay is measured in scroll pixels, not frames.
 *   Each frame, stage_update() receives scroll_dx (pixels advanced this frame)
 *   and decrements the countdown accordingly.  This makes spawn timing
 *   invariant to scroll speed changes — the event fires when the player has
 *   traveled a fixed on-screen distance regardless of current speed.
 */

#include "stage.h"

/* Extra breathing room between consecutive waves to avoid overlap with the
 * previous wave's spawning phase (one spawn every ~8-10 frames). */
#define STAGE_WAVE_EXTRA_DELAY_PX 24u

void stage_init(StagePlayer *p, const StageEvt *script)
{
    p->script = script;
    p->wait = 0;
    p->index = 0;
    /* script == 0 signals procedural / infinite level (no script). */
    p->active = (script != 0) ? 1 : 0;
}

/*
 * stage_update — advance the stage timeline by scroll_dx pixels.
 *
 * Returns a pointer to the event to execute this frame, or NULL if none.
 *
 * STG_WAIT_CLEAR is a blocking gate: it does not advance the script index
 * until (wave_spawning == 0) AND (enemies_active <= evt->a).  Used to ensure
 * the screen is clear before triggering the boss or a high-difficulty act.
 *
 * Only one event is returned per call; if two events have the same pixel
 * offset the second fires on the following frame.
 */
const StageEvt *stage_update(StagePlayer *p, u8 scroll_dx, u8 enemies_active, u8 wave_spawning)
{
    const StageEvt *e;

    if (!p->active || p->script == 0) {
        return 0;
    }

    if (p->wait > 0) {
        /* Delay is in scroll units (pixels). */
        if (scroll_dx >= p->wait) {
            p->wait = 0;
        } else {
            p->wait = (u16)(p->wait - scroll_dx);
        }
        return 0;
    }

    e = &p->script[p->index];

    if (e->cmd == (u8)STG_END) {
        p->active = 0;
        return 0;
    }

    if (e->cmd == (u8)STG_WAIT_CLEAR) {
        if (wave_spawning) {
            return 0;
        }
        if (enemies_active > e->a) {
            return 0;
        }
        /* Gate cleared: consume the event and start its post-clear delay. */
        p->index++;
        p->wait = e->delay;
        return 0;
    }

    p->index++;
    p->wait = e->delay;
    if (e->cmd == (u8)STG_WAVE) {
        /* Slightly relax the cadence between enemy waves. */
        p->wait = (u16)(p->wait + STAGE_WAVE_EXTRA_DELAY_PX);
    }
    return e;
}
