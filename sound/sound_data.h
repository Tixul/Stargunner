/*
 * sound_data.h - Déclarations des assets son (hybrid export PROJECT_*)
 *
 * Part of NGPC Template 2026 (MIT License)
 *
 * Les symboles réels sont namespaced PROJECT_* (format hybrid export).
 * Les macros BGM_NIVEAU_1_*, BGM_NIVEAU_2_*, MENU_BGM_* sont des aliases
 * lisibles pointant vers les symboles PROJECT_*.
 */

#ifndef SOUND_DATA_H
#define SOUND_DATA_H

#include "ngpc_types.h"

/* ---- Stub linker (extern requis par sounds.h) ---- */
extern const unsigned char NOTE_TABLE[];

/* ---- niveau 1 : bgm_stage1 ---- */
extern const unsigned char PROJECT_BGM_STAGE1_NOTE_TABLE[];
extern const unsigned char PROJECT_BGM_STAGE1_BGM_CH0[];
extern const unsigned char PROJECT_BGM_STAGE1_BGM_CH1[];
extern const unsigned char PROJECT_BGM_STAGE1_BGM_CH2[];
extern const unsigned char PROJECT_BGM_STAGE1_BGM_CHN[];
extern const unsigned short PROJECT_BGM_STAGE1_BGM_CH0_LOOP;
extern const unsigned short PROJECT_BGM_STAGE1_BGM_CH1_LOOP;
extern const unsigned short PROJECT_BGM_STAGE1_BGM_CH2_LOOP;
extern const unsigned short PROJECT_BGM_STAGE1_BGM_CHN_LOOP;

/* ---- niveau 2 : bgm_stage2 ---- */
extern const unsigned char PROJECT_BGM_STAGE2_NOTE_TABLE[];
extern const unsigned char PROJECT_BGM_STAGE2_BGM_CH0[];
extern const unsigned char PROJECT_BGM_STAGE2_BGM_CH1[];
extern const unsigned char PROJECT_BGM_STAGE2_BGM_CH2[];
extern const unsigned char PROJECT_BGM_STAGE2_BGM_CHN[];
extern const unsigned short PROJECT_BGM_STAGE2_BGM_CH0_LOOP;
extern const unsigned short PROJECT_BGM_STAGE2_BGM_CH1_LOOP;
extern const unsigned short PROJECT_BGM_STAGE2_BGM_CH2_LOOP;
extern const unsigned short PROJECT_BGM_STAGE2_BGM_CHN_LOOP;

/* ---- menu : menu_test ---- */
extern const unsigned char PROJECT_MENU_TEST_NOTE_TABLE[];
extern const unsigned char PROJECT_MENU_TEST_BGM_CH0[];
extern const unsigned char PROJECT_MENU_TEST_BGM_CH1[];
extern const unsigned char PROJECT_MENU_TEST_BGM_CH2[];
extern const unsigned char PROJECT_MENU_TEST_BGM_CHN[];
extern const unsigned short PROJECT_MENU_TEST_BGM_CH0_LOOP;
extern const unsigned short PROJECT_MENU_TEST_BGM_CH1_LOOP;
extern const unsigned short PROJECT_MENU_TEST_BGM_CH2_LOOP;
extern const unsigned short PROJECT_MENU_TEST_BGM_CHN_LOOP;

/* ---- Aliases lisibles → symboles PROJECT_* ---- */

#define BGM_NIVEAU_1_NOTE_TABLE   PROJECT_BGM_STAGE1_NOTE_TABLE
#define BGM_NIVEAU_1_CH0          PROJECT_BGM_STAGE1_BGM_CH0
#define BGM_NIVEAU_1_CH1          PROJECT_BGM_STAGE1_BGM_CH1
#define BGM_NIVEAU_1_CH2          PROJECT_BGM_STAGE1_BGM_CH2
#define BGM_NIVEAU_1_CHN          PROJECT_BGM_STAGE1_BGM_CHN
#define BGM_NIVEAU_1_CH0_LOOP     PROJECT_BGM_STAGE1_BGM_CH0_LOOP
#define BGM_NIVEAU_1_CH1_LOOP     PROJECT_BGM_STAGE1_BGM_CH1_LOOP
#define BGM_NIVEAU_1_CH2_LOOP     PROJECT_BGM_STAGE1_BGM_CH2_LOOP
#define BGM_NIVEAU_1_CHN_LOOP     PROJECT_BGM_STAGE1_BGM_CHN_LOOP

#define BGM_NIVEAU_2_NOTE_TABLE   PROJECT_BGM_STAGE2_NOTE_TABLE
#define BGM_NIVEAU_2_CH0          PROJECT_BGM_STAGE2_BGM_CH0
#define BGM_NIVEAU_2_CH1          PROJECT_BGM_STAGE2_BGM_CH1
#define BGM_NIVEAU_2_CH2          PROJECT_BGM_STAGE2_BGM_CH2
#define BGM_NIVEAU_2_CHN          PROJECT_BGM_STAGE2_BGM_CHN
#define BGM_NIVEAU_2_CH0_LOOP     PROJECT_BGM_STAGE2_BGM_CH0_LOOP
#define BGM_NIVEAU_2_CH1_LOOP     PROJECT_BGM_STAGE2_BGM_CH1_LOOP
#define BGM_NIVEAU_2_CH2_LOOP     PROJECT_BGM_STAGE2_BGM_CH2_LOOP
#define BGM_NIVEAU_2_CHN_LOOP     PROJECT_BGM_STAGE2_BGM_CHN_LOOP

#define MENU_NOTE_TABLE           PROJECT_MENU_TEST_NOTE_TABLE
#define MENU_BGM_CH0              PROJECT_MENU_TEST_BGM_CH0
#define MENU_BGM_CH1              PROJECT_MENU_TEST_BGM_CH1
#define MENU_BGM_CH2              PROJECT_MENU_TEST_BGM_CH2
#define MENU_BGM_CHN              PROJECT_MENU_TEST_BGM_CHN
#define MENU_BGM_CH0_LOOP         PROJECT_MENU_TEST_BGM_CH0_LOOP
#define MENU_BGM_CH1_LOOP         PROJECT_MENU_TEST_BGM_CH1_LOOP
#define MENU_BGM_CH2_LOOP         PROJECT_MENU_TEST_BGM_CH2_LOOP
#define MENU_BGM_CHN_LOOP         PROJECT_MENU_TEST_BGM_CHN_LOOP

/* ---- SFX ---- */
extern const u8 SFX_COUNT;

#endif /* SOUND_DATA_H */
