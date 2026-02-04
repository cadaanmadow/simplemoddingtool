Simple Modding Tool
===================

A lightweight mod manager for games that use loose files or Paks folders.

Features:
- Enable / disable mods without deleting files
- Supports multiple games
- Add and delete mod files directly
- Simple and beginner-friendly UI
- No admin required

How to use:
1. Run Simple Modding Tool.exe
2. Click "Add Game Mod Folder"
3. Select your game's Mods or Paks folder
4. Add mod files or toggle them on/off

Disabled mods are moved to:
Mods_DISABLED

Notes:
- This tool does not modify game executables
- Works with most Unreal Engine and loose-file games
- Portable (no installation)

## Building from source (optional)

This project can be built into a standalone Windows executable using PyInstaller.

Requirements:
- Python 3.10+
- PySide6
- PyInstaller

Build command:
pyinstaller --name "Simple Modding Tool" --noconsole --icon=mod_manager.ico --clean mod_manager.py

## Download exe from Nexus Mods

https://www.nexusmods.com/mortalkombat/mods/1544?tab=description


