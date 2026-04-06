/*
 * dma_raster_example.c - ngpc_dma_raster usage example
 *
 * Part of NGPC Template 2026 (MIT License)
 *
 * Documentation-by-example. Not compiled by default.
 */

#include "../src/core/ngpc_sys.h"
#include "../src/core/ngpc_timing.h"
#include "../src/fx/ngpc_dma.h"
#include "../src/fx/ngpc_dma_raster.h"

/* Example: parallax X scroll on SCR1 using MicroDMA (Timer0/HBlank).
 *
 * This gives you a per-scanline scroll effect without a CPU HBlank ISR. */
void example_dma_raster_parallax_scr1(void)
{
    static u8 scr1_x[152];
    static NgpcDmaRaster r;

    /* 3 bands: sky (0.25x), mid (0.5x), ground (1.0x) */
    static const RasterBand bands[] = {
        {  0,  64 },
        { 50, 128 },
        { 100, 256 }
    };

    u16 camera_x = 0;

    ngpc_dma_init();
    ngpc_dma_raster_begin(&r, GFX_SCR1, scr1_x, (const u8 NGP_FAR *)0);
    ngpc_dma_raster_enable(&r);

    for (;;) {
        camera_x++;

        /* Build the 152-byte table in RAM (any pattern is fine). */
        ngpc_dma_raster_build_parallax_table(scr1_x, bands, 3, camera_x);

        /* VBlank sync + one-shot re-arm (do this early). */
        ngpc_vsync();
        ngpc_dma_raster_rearm(&r);
    }
}

