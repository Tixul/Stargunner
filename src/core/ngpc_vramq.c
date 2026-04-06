/*
 * ngpc_vramq.c - Queued VRAM updates flushed during VBlank
 *
 * Part of NGPC Template 2026 (MIT License)
 *
 * Problem this solves: writing to VRAM during active display causes graphical
 * glitches (tearing, corruption) on real hardware.  The queue lets game code
 * enqueue tile/palette writes during the active frame, then the VBlank ISR
 * drains all commands at once (ngpc_vramq_flush in ngpc_sys.c isr_vblank).
 *
 * Concurrency protection:
 *   s_lock is a flag to guard the command list.  If ngpc_vramq_flush() is
 *   called from the VBL ISR while the main code is mid-enqueue, the flush
 *   is skipped that frame.  Commands accumulate until the next VBL.
 *   This is safe because TLCS-900 interrupts are not re-entrant.
 */

#include "ngpc_hw.h"
#include "ngpc_vramq.h"

#define VRAM_ADDR_MIN  0x8000
#define VRAM_ADDR_MAX  0xBFFF

#define CMD_COPY  1
#define CMD_FILL  2

/* Compact command storage:
 * - dst is stored as 16-bit address (VRAM is in 0x8000-0xBFFF, fits in u16)
 * - copy source uses full 24-bit pointer (ROM data at 0x200000+)
 */
static u8                s_cmd_type[VRAMQ_MAX_CMDS];
static u16               s_cmd_dst[VRAMQ_MAX_CMDS];
static u16               s_cmd_len[VRAMQ_MAX_CMDS];
static const u16        *s_cmd_src[VRAMQ_MAX_CMDS];
static u16               s_cmd_fill[VRAMQ_MAX_CMDS];
static volatile u8       s_cmd_count;
static volatile u8       s_drop_count;
static volatile u8       s_lock;

static u8 dst_range_ok(volatile u16 *dst, u16 len_words)
{
    u32 start;
    u32 bytes;
    u32 end;

    if (!dst || len_words == 0)
        return 0;

    start = (u32)(u16)(u32)dst;
    bytes = (u32)len_words << 1;
    end = start + bytes - 1;

    if (start < VRAM_ADDR_MIN) return 0;
    if (end > VRAM_ADDR_MAX) return 0;
    return 1;
}

void ngpc_vramq_init(void)
{
    s_cmd_count = 0;
    s_drop_count = 0;
    s_lock = 0;
}

u8 ngpc_vramq_copy(volatile u16 *dst, const u16 *src, u16 len_words)
{
    u8 idx;

    if (!src || !dst_range_ok(dst, len_words))
        return 0;

    s_lock = 1;
    idx = s_cmd_count;
    if (idx >= VRAMQ_MAX_CMDS) {
        s_drop_count++;
        s_lock = 0;
        return 0;
    }

    s_cmd_dst[idx] = (u16)(u32)dst;
    s_cmd_len[idx] = len_words;
    s_cmd_src[idx] = src;
    s_cmd_fill[idx] = 0;
    s_cmd_type[idx] = CMD_COPY;
    s_cmd_count = (u8)(idx + 1);
    s_lock = 0;

    return 1;
}

u8 ngpc_vramq_fill(volatile u16 *dst, u16 value, u16 len_words)
{
    u8 idx;

    if (!dst_range_ok(dst, len_words))
        return 0;

    s_lock = 1;
    idx = s_cmd_count;
    if (idx >= VRAMQ_MAX_CMDS) {
        s_drop_count++;
        s_lock = 0;
        return 0;
    }

    s_cmd_dst[idx] = (u16)(u32)dst;
    s_cmd_len[idx] = len_words;
    s_cmd_src[idx] = (const u16 *)0;
    s_cmd_fill[idx] = value;
    s_cmd_type[idx] = CMD_FILL;
    s_cmd_count = (u8)(idx + 1);
    s_lock = 0;

    return 1;
}

void ngpc_vramq_flush(void)
{
    u8 i;
    u8 count;

    if (s_lock)
        return;

    count = s_cmd_count;
    if (count == 0)
        return;

    s_lock = 1;

    for (i = 0; i < count; i++) {
        volatile u16 *dst = (volatile u16 *)(u32)s_cmd_dst[i];
        u16 len = s_cmd_len[i];

        if (s_cmd_type[i] == CMD_COPY) {
            const u16 *src = s_cmd_src[i];
            while (len--) {
                *dst++ = *src++;
            }
        } else if (s_cmd_type[i] == CMD_FILL) {
            u16 v = s_cmd_fill[i];
            while (len--) {
                *dst++ = v;
            }
        }
    }

    s_cmd_count = 0;
    s_lock = 0;
}

void ngpc_vramq_clear(void)
{
    if (s_lock)
        return;
    s_cmd_count = 0;
}

u8 ngpc_vramq_pending(void)
{
    return s_cmd_count;
}

u8 ngpc_vramq_dropped(void)
{
    return s_drop_count;
}

void ngpc_vramq_clear_dropped(void)
{
    s_drop_count = 0;
}

