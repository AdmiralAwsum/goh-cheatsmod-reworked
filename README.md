# Gates of Hell: Ostfront - CheatsMod 2.6 Reworked (v1.069.0 + MACE)

An English-only, modernized rework of **CheatsMod 2.6** for **Call to Arms - Gates of Hell: Ostfront (v1.069.0)** and **MACE** (plus BM Mod, 01 WAVE, Realism Sound Pack, Mount Everything, and Conquest).

See [CHANGELOG.md](./CHANGELOG.md) for the full list of fixes and changes.

## Install

1. Copy the `mod/` folder into your game's `mods/` directory and rename it (for example, `Call to Arms - Gates of Hell\mods\cheatsmod_26_1069_fix`).
2. In the in-game **Mods** menu, disable the original Steam Workshop `CheatsMod 2.6` and activate **CheatsMod 2.6 (1.069 + Conquest Fix)** **last** in your load order.

### Recommended Load Order (with MACE)

1. `MACE`
2. `BM Mod - Gates of Hell`
3. `BM Mod - MACE Compat Patch`
4. `Everything Stays - MACE`
5. `BM Mod + Everything Stays - MACE Compat` *(optional merged `entitymanager.set`)*
6. `01 WAVE`
7. `Gates of Hell: Ostfront - Realism Sound Pack - by OSCARMIKE`
8. `Increased call-in stages and instant deployment for conquest`
9. `Mount Everything`
10. `CheatsMod 2.6 (1.069 + Conquest Fix)` *(keep last)*

## Features & Fixes

* **Persistent UI in Conquest (v1.069.0 `SceneGameView.xml`):**
  * Moved `gui_gc_reinforcement` into an independent upper-right panel (`cheat_reinforcement_layer`) outside `unitspawn_layer`, so the Cheat Menu **never disappears** when all Conquest call-in waves are deployed.
* **Automatic Human Player Detection (Solo & Co-op/Multiplayer):**
  * Automatically detects the active human player slot (`0`–`7`) at mission start via `autoassign` + Conquest's `_user` tag, and targets all human players in Co-op/MP without buffing AI bots.
* **100% English Localization:**
  * Removed `_说明.txt`, rewrote `singlecheats.pot` (`Language: en`), and cleaned all hardcoded Chinese strings from `cheats.mi`, `m_cheats.mi`, and `option_tags.mi`.
* **Conquest Quality-of-Life:**
  * **Instant Win (Conquest):** Triggers `gameover_request_player_win$ = 1` to finish and win the active Conquest battle immediately with full rewards.
  * **2000 CP Call-In Budget:** `resources_*.set` starts with `2000` CP (`Limit 2000`, `PointsPerSecond 2.0`) so all 5 waves, airstrikes, and emplacements can be deployed immediately.
* **Fixed & Reworked Cheats:**
  * **Max Veterancy:** Sets all alive friendly infantry, gun crews, and vehicle crews to Level 8 (`veterancy 8`).
  * **Instant Vehicle Repair (`Repair All Vehicles`):** Restores `body`, `turret`, `gun`, `engine`, `trackleft`, `trackright`, `wheel`, `shield`, `mantlet`, and `cabin` to `work`.
  * **Instakill & Range/Accuracy (`extension.mod`):** Fixed broken MoW:AS2 modifier syntax to valid v1.069.0 syntax (`armor {scale 0.01}`, `aim_range {scale 3}`, `accuracy {scale 5}`), fixed swapped Aimrange ON/OFF icons, and added `1s`–`1.5s` delays to continuous loops.
  * **Destroy Enemy Armor:** Re-enabled trigger with `{count -1}` across all player slots.
  * **Fast Mines + Shift-Queueable Engineer:** Direct mine spawn drops **8 armed mines** in `0.2s`, and the new **Fast Mine Engineer** in the Support menu spawns with **40 AT + 40 AP lightweight instant-plant (`0.1s`) mines** so you can hold **Shift** and queue entire minefields.
  * **FPS-Friendly Ammo Box & Working Infinite Ammo:** Replaced the laggy 300-item scan with MACE's native `/properties/resupply.inc` (`radius 30`, `resupplyPeriod 3`) and fixed Infinite Ammo to spawn/remove an invisible global resupply entity (`radius 500`).

## Rebuilding from Source

The `scripts/` folder contains the Python scripts used to build and patch the `.pak` archives from a local Gates of Hell `v1.069.0` + MACE installation:

* `scripts/build_base_1069.py` — extracts fresh `v1.069.0` + MACE `.mi` maps and patches `SceneGameView.xml`.
* `scripts/rework_cheatsmod.py` — applies the English translation, player auto-detection, Conquest instant win/budget, fast mines, and trigger/modifier fixes to `mod/`.
