# Catppuccin Macchiato for IW4x

A full-UI [Catppuccin Macchiato](https://catppuccin.com/palette) theme for [IW4x](https://iw4x.io) (Call of Duty: Modern Warfare 2, 2009) — plus an optional pack of trickshot and tryhard classes with coloured names.

- Solid Macchiato backgrounds instead of the soldier art, clouds, glows and fog
- Menus recoloured to Catppuccin text/accent colours with a mauve selection highlight
- Popups become flat slate panels
- Console, scoreboard ping bars and sprint meter themed too
- Weapon/perk icons, emblems and map previews are left untouched so they still read correctly
- Everything lives in `userraw\` — no game files are modified, and it uninstalls in one click

## Install

1. Install IW4x first ([docs.iw4x.io](https://docs.iw4x.io)) and launch it at least once.
2. Download the latest `iw4x-catppuccin-*.zip` from **Releases** and extract it anywhere.
3. **Close the game**, then double-click **`install.bat`**.

The installer finds your game through your Steam libraries (or asks for the folder). You can also pass it directly:

```bat
install.bat "D:\SteamLibrary\steamapps\common\Call of Duty Modern Warfare 2"
```

## Uninstall

Close the game and double-click **`uninstall.bat`**. It removes the theme files and restores your original console/HUD colours exactly as they were.

## Optional: class pack

Overwrites custom classes 1–11 with ready-made loadouts. In game, open the console (`~`) and type:

```
exec ctp_classes
```

| # | Name | Loadout |
|---|---|---|
| 1 | Rainbow Snipe (animated) | Intervention FMJ + Akimbo 1887s · Sleight of Hand / Lightweight / Commando |
| 2 | Quickscope God | Intervention FMJ · Sleight of Hand / Stopping Power / Commando |
| 3 | CoD4 R700 Flicks | IW4x's CoD4 R700 + Tac Knife · Marathon / Lightweight / Commando |
| 4 | Barrett Bounces | Barrett FMJ + SPAS-12 · Sleight of Hand / Lightweight / Commando |
| 5 | WA2000 Snaps | WA2000 FMJ + Tac Knife + Tactical Insertion |
| 6 | OMA Canswap | Intervention + One Man Army for class-swap tricks |
| 7 | UMP Silent Rush | UMP45 Silencer/Rapid Fire · Marathon / Lightweight / Ninja |
| 8 | ACR Laser Beam | ACR Holo/FMJ · Scavenger / Stopping Power / Ninja |
| 9 | Tube Tryhard (animated) | M4 Tube + One Man Army · Danger Close / Martyrdom |
| 10 | Akimbo 1887s | Riot shield on your back + Akimbo 1887s |
| 11 | Tac Knife Ninja | MP5K + USP Tac Knife · Marathon / Lightweight / Commando |

Uninstalling the theme doesn't touch your classes — change them in Create-a-Class as usual.

## Notes

- **Built for IW4x r5154.** The theme ships recoloured copies of IW4x's own menus, so after an IW4x update the installer warns you, and menus that IW4x changed keep the older layout until the theme is rebuilt (see below).
- The in-match HUD and a few rarely-seen screens (end-of-match summaries, challenge lists, attachment pickers) keep stock colours but still get the solid backgrounds. IW4x re-parses every disk menu into an 11 MB memory pool when a map loads, and theming everything overflows it.
- Works on any server — `userraw` cosmetics are client-side only.

## Rebuilding (after an IW4x update)

Requires Python 3 with Pillow, and an IW4x install (the launcher provides `Unlinker.exe`, which dumps the stock menus).

```bat
pip install pillow
python builder\rebuild.py "C:\...\Call of Duty Modern Warfare 2"
```

This regenerates `userraw\z_catppuccin.iwd` from your current game files; run `install.bat` afterwards. `builder\gen_classes.py` regenerates the class pack.

## Credits & licence

- Colours: [Catppuccin](https://github.com/catppuccin/catppuccin) (MIT).
- Menus are recoloured from [IW4x](https://github.com/iw4x) (GPL-3.0) and Modern Warfare 2's own menu definitions, dumped with [OpenAssetTools](https://github.com/Laupetin/OpenAssetTools)' Unlinker. Modern Warfare 2 © Activision; you need your own copy of the game.
- This project is licensed under GPL-3.0 (see `LICENSE`).
