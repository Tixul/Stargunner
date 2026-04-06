@echo off
cls

REM ============================================================
REM  NGPC Template 2026 - Build script (Windows)
REM  MIT License
REM
REM  CONFIGURATION: Edit the paths below to match your setup.
REM ============================================================

REM --- Toolchain path (Toshiba cc900 compiler) ---
SET compilerPath=C:\t900

REM --- Path to system.lib (required for CLR_FLASH_RAM — block 33 save workaround for BIOS bug) ---
SET systemLibPath=C:\Users\wilfr\Desktop\NGPC_RAG\04_MY_PROJECTS\NeoGeo_Windcup\system.lib

REM --- ROM name (also update CartTitle in src/core/carthdr.h) ---
SET romName=main

REM --- Pad ROM to 2MB for flash carts? (1=yes, 0=no) ---
SET ResizeRom=1

REM --- Launch emulator after build? (1=yes, 0=no) ---
SET Run=1

REM --- Emulator executable path ---
SET emuPath="C:\emu\NeoPop\NeoPop-Win32.exe"

REM ============================================================
REM  BUILD (do not edit below unless you know what you're doing)
REM ============================================================

SET THOME=%compilerPath%
SET BinPath=bin
SET romExt=ngc
SET rootPath=%~dp0
path=%path%;%THOME%\bin

echo [NGPC Template 2026] Building...

if not "%systemLibPath%"=="" (
    make -f makefile clean SYSTEM_LIB="%systemLibPath%"
    make -f makefile SYSTEM_LIB="%systemLibPath%"
    make -f makefile move_files SYSTEM_LIB="%systemLibPath%"
) else (
    make -f makefile clean
    make -f makefile
    make -f makefile move_files
)

if "%ResizeRom%"=="1" (
    if exist "%~dp0utils\NGPRomResize.exe" (
        echo [NGPC Template 2026] Resizing ROM to 2MB...
        MOVE "%~dp0%BinPath%\%romName%.%romExt%" "%~dp0%BinPath%\_%romName%.%romExt%" >nul 2>&1
        "%~dp0utils\NGPRomResize.exe" "%~dp0%BinPath%\_%romName%.%romExt%"
        MOVE "%~dp0%BinPath%\_%romName%.%romExt%" "%~dp0%BinPath%\%romName%.%romExt%" >nul 2>&1
        DEL "%~dp0%BinPath%\2MB__%romName%.%romExt%" >nul 2>&1
    ) else (
        echo [NGPC Template 2026] Skip resize: utils\NGPRomResize.exe not found.
    )
)

if "%Run%"=="1" (
    if exist %emuPath% (
        echo [NGPC Template 2026] Launching emulator...
        %emuPath% "%rootPath:~0,-1%.\%BinPath%\%romName%.%romExt%"
    ) else (
        echo [NGPC Template 2026] Skip run: emulator not found at %emuPath%.
    )
)

echo [NGPC Template 2026] Done.
