# Changelog

## 2.6 Reworked (v1.069.0)

* **UI & Map Update (v1.069.0):**
  * Rebuilt `SceneGameView.xml` from base game `v1.069.0` with an independent `cheat_reinforcement_layer` so the Cheat Menu persists after all Conquest waves are called in.
  * Rebuilt `resource/map/multi.pak` (388 maps, preserving MACE's 16 Frontlines maps) and `resource/map/single.pak` (91 missions) from `v1.069.0` + MACE.
* **Auto Player Detection & Co-op Support:**
  * Added `cheats/auto_detect_player` using `autoassign` + `_user` tag detection across player slots `0`–`7`.
  * Updated friendly cheat selectors to target `{select {player "X"} {tag _user}}`.
* **English-Only Cleanup:**
  * Removed `_说明.txt`, translated `singlecheats.pot` to English (`Language: en`), and stripped Chinese labels from `cheats.mi`, `m_cheats.mi`, and `option_tags.mi`.
* **Conquest Additions:**
  * Added **Instant Win (Conquest)** button (`gameover_request_player_win$ = 1`).
  * Added `resources_*.set` with `2000` starting/max CP and `2.0` CP/sec regeneration.
* **Cheat & Performance Fixes:**
  * Fixed `extension.mod` syntax for Instakill (`armor {scale 0.01}`) and Range & Accuracy (`aim_range {scale 3}`, `accuracy {scale 5}`), and fixed swapped Aimrange ON/OFF icons.
  * Added `cheats/active/repair` trigger and exposed **Repair All Vehicles** in the Cheats menu.
  * Re-enabled `cheats/destroyarmor` with `{count -1}`.
  * Fixed **Max Veterancy** (`veterancy 8`) selector to include vehicle/gun crews and Conquest `_user` units.
  * Added **Fast Mine Engineer** (40 AT + 40 AP `0.1s` mines, Shift-queueable) and doubled direct mine spawns to 8 mines per click with `0.2s` arming.
  * Rewrote `cheat_supply.inc` using MACE's `/properties/resupply.inc` to eliminate FPS drops and added working **Infinite Ammo** global resupply entity.
