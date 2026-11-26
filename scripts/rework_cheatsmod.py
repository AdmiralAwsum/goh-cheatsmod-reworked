import glob
import io
import math
import os
import re
import zipfile
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

MOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mod")
GOH_DIR = os.environ.get("GOH_DIR", r"D:\SteamLibrary\steamapps\common\Call to Arms - Gates of Hell")


def remove_chinese_docs():
    cn_doc = os.path.join(MOD, "_说明.txt")
    if os.path.exists(cn_doc):
        os.remove(cn_doc)
        print("Removed _说明.txt")


def rewrite_localization():
    pot_path = os.path.join(MOD, "localizations", "default", "interface", "text", "mission", "singlecheats.pot")
    with open(pot_path, "r", encoding="utf-8", errors="replace") as f:
        old_lines = f.read().splitlines()

    # Clean English overrides for internal key names
    en_overrides = {
        "c_aimrange_0": "Enabled: Max Range & Accuracy",
        "c_fuel_0": "Enabled: Infinite Fuel & Stamina",
        "c_godmode_0": "Enabled: God Mode (Infinite Health & Armor)",
        "c_infammo_0": "Enabled: Infinite Ammo (Map-Wide Resupply)",
        "c_setplayer_0": "Active Player set to: <e(shadow)><c(ff0000)>1</c></e>",
        "c_setplayer_1": "Active Player set to: <e(shadow)><c(00d319)>2</c></e>",
        "c_setplayer_2": "Active Player set to: <e(shadow)><c(f2c200)>3</c></e>",
        "c_setplayer_3": "Active Player set to: <e(shadow)><c(ffffff)>0</c></e>",
        "c_setplayer_4": "Active Player set to: <e(shadow)><c(0000ff)>4</c></e>",
        "c_setplayer_5": "Active Player set to: <e(shadow)><c(ff0000)>5</c></e>",
        "c_setplayer_6": "Active Player set to: <e(shadow)><c(00d319)>6</c></e>",
        "c_setplayer_7": "Active Player set to: <e(shadow)><c(f2c200)>7</c></e>",
        "c_weakenemy_0": "Enabled: Instakill Enemies (Infantry & Vehicles)",
        "cheatversion": "<s(25)><c(204 204 204)>CheatsMod <c(40c040)>2.6 Reworked<c(204 204 204)><s(8)>",
        "cheatversion1": "<c(40c040)>v2.6 Reworked",
        "c_deactivated_0": "Cheat Deactivated",
        "cheats_option_select": "Cheat Settings:",
        "Autoassign": "<e(shadow)><c(f2c200)>Auto-Assign</c></e>",
        "Set to player0": "Cheats & spawns target Player 0 (auto-detected; click to switch to Player 1)",
        "Set to player1": "Cheats & spawns target Player 1 (auto-detected; click to switch to Player 2)",
        "Set to player2": "Cheats & spawns target Player 2 (auto-detected; click to switch to Player 3)",
        "Set to player3": "Cheats & spawns target Player 3 (auto-detected; click to switch to Player 4)",
        "Set to player4": "Cheats & spawns target Player 4 (auto-detected; click to switch to Player 5)",
        "Set to player5": "Cheats & spawns target Player 5 (auto-detected; click to switch to Player 6)",
        "Set to player6": "Cheats & spawns target Player 6 (auto-detected; click to switch to Player 7)",
        "Set to player7": "Cheats & spawns target Player 7 (auto-detected; click to switch to Player 0)",
        "Deploy mines": "AT Mines (x8)",
        "Lay a mine field": "Click on the ground to drop 8 armed Anti-Tank mines",
        "Fast Miner": "Fast Mine Engineer",
        "Fast Miner hint": "Click on ground to spawn Engineer with 40 AT + 40 AP instant (0.1s) mines. Hold Shift to queue!",
        "Support": "Ammo Boxes, Fast Mine Engineer, AT/AP Mines, Artillery, Mortar & Cleanup",
        "Cheats below effects enemy": "Cheats below target enemy units on the map",
        "Destroy enemy armor": "Break gun, turret, engine & tracks on all enemy vehicles",
    }

    out = []
    for line in old_lines:
        if line.startswith('"Language:'):
            out.append('"Language: en\\n"')
            continue
        if line.startswith('msgstr "'):
            out.append('msgstr "Configure CheatsMod"')
            continue
        m = re.match(r'^(\t\{"([^"]+)"\s+)"(.*)"(\})\s*$', line)
        if m:
            prefix, key, val, suffix = m.groups()
            if key in en_overrides:
                new_val = en_overrides[key]
            else:
                # Use the clean English key itself
                new_val = key
            out.append(f'{prefix}"{new_val}"{suffix}')
        else:
            out.append(line)

    # Insert Fast Miner + missing player4..7 & c_setplayer_4..7 tags before final '}'
    extra_tags = [
        '\t{"Fast Miner" "Fast Mine Engineer"}',
        '\t{"Fast Miner hint" "Click on ground to spawn Engineer with 40 AT + 40 AP instant (0.1s) mines. Hold Shift to queue!"}',
        '\t{"Set to player4" "Cheats & spawns target Player 4 (auto-detected; click to switch to Player 5)"}',
        '\t{"Set to player5" "Cheats & spawns target Player 5 (auto-detected; click to switch to Player 6)"}',
        '\t{"Set to player6" "Cheats & spawns target Player 6 (auto-detected; click to switch to Player 7)"}',
        '\t{"Set to player7" "Cheats & spawns target Player 7 (auto-detected; click to switch to Player 0)"}',
        '\t{"c_setplayer_4" "Active Player set to: <e(shadow)><c(0000ff)>4</c></e>"}',
        '\t{"c_setplayer_5" "Active Player set to: <e(shadow)><c(ff0000)>5</c></e>"}',
        '\t{"c_setplayer_6" "Active Player set to: <e(shadow)><c(00d319)>6</c></e>"}',
        '\t{"c_setplayer_7" "Active Player set to: <e(shadow)><c(f2c200)>7</c></e>"}',
    ]
    existing = "\n".join(out)
    for idx in range(len(out) - 1, -1, -1):
        if out[idx].strip() == "}":
            pos = idx
            for tag_line in extra_tags:
                key = tag_line.split('"')[1]
                if f'"{key}"' not in existing:
                    out.insert(pos, tag_line)
                    pos += 1
            break

    result = "\r\n".join(out) + "\r\n"
    assert not re.search(r"[\u4e00-\u9fff]", result), "Chinese still found in singlecheats.pot!"
    with open(pot_path, "w", encoding="utf-8", newline="") as f:
        f.write(result)
    print("Rewrote singlecheats.pot in pure English.")


def rewrite_supply_and_entities():
    # 1. Universal cheat_supply.inc using supply_ammo(0) from whichever resupply.inc is loaded
    # (works on Vanilla, MACE, Valour, etc. without crashing on MACE-only items_light_jap!)
    supply_inc = """(include "/properties/resupply.inc")

(define "cheat_supply_ammo"
\t("supply_ammo" supply(0))
\t{extender "supply_zone"
\t\t{fuel \t{amount 5}\t{value 1}}
\t\t{resupply
\t\t\t("items_explosives")
\t\t\t("items_engineer")
\t\t\t("items_medic")
\t\t}
\t\t{radius\t\t\t\t30}
\t\t{resupplyPeriod\t\t3}
\t\t{regenerationPeriod 0}
\t\t{limit\t\t\t\t0}
\t}
)

(define "cheat_supply_ammo_global"
\t("supply_ammo" supply(0))
\t{extender "supply_zone"
\t\t{fuel \t{amount 10}\t{value 1}}
\t\t{resupply
\t\t\t("items_medic")
\t\t}
\t\t{radius\t\t\t\t500}
\t\t{resupplyPeriod\t\t5}
\t\t{regenerationPeriod 0}
\t\t{limit\t\t\t\t0}
\t}
)
"""
    with open(os.path.join(MOD, "resource", "cheats", "cheat_supply.inc"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(supply_inc)
    print("Rewrote cheat_supply.inc (MACE-native, lightweight, FPS-friendly).")

    # 2. Update entity.pak: instant-plant mines + ammo_cheatsmod_global
    mine_at_def = """{actor
\t(include "/properties/stuff_mine.ext")
\t{extension "mine_m1a1.mdl"}
\t{extender "stuff"
\t\t{item "mine m1a1_cheat"}
\t}
\t{extender "mine"
\t\t{time 0.1}
\t}
\t{collider "mine.at"}
\t{props "antitank" "cheat_mine_drop"}
\t(include "/properties/shadow/round.inc")
\t{Obstacle "body"
\t\t{Circle2
\t\t\t{Radius 7.5}
\t\t}
\t}
\t{Volume "body"
\t\t{density 0}
\t}
}
"""
    mine_ap_def = """{actor
\t(include "/properties/stuff_mine.ext")
\t{extension "mine_s.mdl"}
\t{extender "stuff"
\t\t{item "mine s_cheat"}
\t}
\t{extender "mine"
\t\t{time 0.1}
\t}
\t{collider "mine.ap"}
\t{props "bounding" "antipersonnel" "cheat_mine_drop"}
\t{Obstacle "body"
\t\t{Circle2
\t\t\t{Radius 20}
\t\t}
\t}
\t{Volume "body"
\t\t{density 0}
\t}
}
"""
    ammo_global_def = """{actor
\t(include "/properties/ammo_box.ext")
\t(include "/cheats/cheat_supply.inc")
\t{extension "../ammo_cheatsmod/inf_crate.mdl"}
\t{props "vision_lev00_can" "ammo_crate" "no_recrew_logic" "cheatsmod_inf_ammo"}
\t("cheat_supply_ammo_global")
\t{extender "inventory"
\t\t{Box
\t\t}
\t}
\t{mass 100}
}
"""
    ent_pak = os.path.join(MOD, "resource", "entity", "entity.pak")
    tmp_pak = ent_pak + ".tmp"
    at_assets = {}
    ap_assets = {}
    with zipfile.ZipFile(ent_pak, "r") as zin:
        for item in zin.infolist():
            nl = item.filename.lower()
            if nl.endswith("/") or nl.endswith(".def"):
                continue
            if nl.startswith("inventory/mine_antitank/") or nl.startswith("inventory/mine_antitank_cheat/"):
                at_assets[os.path.basename(item.filename)] = zin.read(item.filename)
            elif nl.startswith("inventory/mine_ap/") or nl.startswith("inventory/mine_s_cheat/"):
                ap_assets[os.path.basename(item.filename)] = zin.read(item.filename)
    assert "mine_m1a1.mdl" in at_assets, f"Missing mine_m1a1.mdl in entity.pak (keys={list(at_assets)})"
    assert "mine_s.mdl" in ap_assets, f"Missing mine_s.mdl in entity.pak (keys={list(ap_assets)})"

    with zipfile.ZipFile(ent_pak, "r") as zin, zipfile.ZipFile(tmp_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            nl = item.filename.lower()
            if (
                nl.startswith("inventory/mine_antitank/")
                or nl.startswith("inventory/mine_antitank_cheat/")
                or nl.startswith("inventory/mine_ap/")
                or nl.startswith("inventory/mine_s_cheat/")
                or nl == "service/ammo_cheatsmod_global/ammo_cheatsmod_global.def"
            ):
                continue
            zout.writestr(item, zin.read(item.filename))
        for fname, data in at_assets.items():
            zout.writestr(f"inventory/mine_antitank_cheat/{fname}", data)
        zout.writestr("inventory/mine_antitank_cheat/mine_antitank_cheat.def", mine_at_def.encode("utf-8"))
        for fname, data in ap_assets.items():
            if fname.lower() == "s_mine.mtl":
                data = data.replace(b'{diffuse "mine_s_cheat"}', b'{diffuse "s_mine"}')
            zout.writestr(f"inventory/mine_s_cheat/{fname}", data)
        zout.writestr("inventory/mine_s_cheat/mine_s_cheat.def", mine_ap_def.encode("utf-8"))
        zout.writestr("service/ammo_cheatsmod_global/ammo_cheatsmod_global.def", ammo_global_def.encode("utf-8"))
    os.replace(tmp_pak, ent_pak)
    print("Updated entity.pak (matching mine folders + cheat_mine_drop/cheatsmod_inf_ammo props).")

    # 3. Update gamelogic.pak: add fast lightweight m1a1_cheat.mine & s_cheat.mine stuff definitions
    m1a1_cheat_mine = """{from "pattern antitank"
\t{entity "mine_antitank_cheat"}
\t{inventory {size 1 1}}
\t{mass 0.1}
}
"""
    s_cheat_mine = """{from "pattern antipersonnel"
\t{entity "mine_s_cheat"}
\t{inventory {size 1 1}}
\t{mass 0.1}
\t{damage blastwave
\t\t{energy 1.0}
\t\t{area 0.6 2}
\t\t{ground_interaction_radius 0.1}
\t}
\t{damage add blastwave
\t\t{energy 0.51}
\t\t{area 3 5}
\t\t{ground_interaction_radius 0}
\t}
\t{damage add blastwave
\t\t{energy 0.25}
\t\t{area 6 8}
\t\t{ground_interaction_radius 0}
\t}
}
"""
    gl_pak = os.path.join(MOD, "resource", "gamelogic.pak")
    tmp_gl = gl_pak + ".tmp"
    with zipfile.ZipFile(gl_pak, "r") as zin, zipfile.ZipFile(tmp_gl, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.lower() in ("set/stuff/explosive/m1a1_cheat.mine", "set/stuff/explosive/s_cheat.mine"):
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("set/stuff/explosive/m1a1_cheat.mine", m1a1_cheat_mine.encode("utf-8"))
        zout.writestr("set/stuff/explosive/s_cheat.mine", s_cheat_mine.encode("utf-8"))
    os.replace(tmp_gl, gl_pak)
    print("Updated gamelogic.pak with m1a1_cheat.mine & s_cheat.mine.")


def make_addexp_trigger():
    # Promote ONLY the active cheat_options-player$ slot (never AI bots!).
    # Omit {prop human} filter so actor_state targets all alive entities owned by the player
    # (infantry, gun crews, open-top crews, and vehicles) without excluding inactive/linked crews.
    blocks = []
    for p in range(8):
        blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"actor_state"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{player
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state dead}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{human
\t\t\t\t\t\t\t\t{{veterancy 8}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")
    inner = "\n".join(blocks)
    return f"""\t\t\t{{"cheats/active/addexp"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/addexp"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{inner}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/addexp"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/addexp"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_auto_detect_player_trigger(is_dcg=False):
    """Polls every 1.0s until the human player slot is identified, then locks cheat_options-player$ and cheat_enemyspawn$.

    When is_dcg=True (Conquest maps containing dcg_vars.inc):
      Priority 1: read id_1st_player$ (set by GoH Conquest Lua OnGameStart at t=0s).
      Priority 2: check user_control entities in slot order 1..7 then 0, excluding AI slots
      (enemyid$, id_1st_enemy$, id_defenderbot$).
    When is_dcg=False (Singleplayer / Skirmish / Frontlines without dcg_vars.inc):
      Zero Conquest-only variable references — pure user_control entity detection in slot order 1..7 then 0.
    """
    conquest_cases = []
    if is_dcg:
        for p in range(1, 8):
            conquest_cases.append(f"""\t\t\t\t\t\t{{"case"
\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t{{var "id_1st_player$"}}
\t\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_enemyspawn$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}""")

    fallback_checks = []
    for p in (1, 2, 3, 4, 5, 6, 7, 0):
        set_block = f"""\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t{{var "cheat_enemyspawn$"}}
\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t\t\t}}"""
        if not is_dcg or p == 0:
            inner_guard = set_block
        else:
            inner_guard = f"""\t\t\t\t\t\t\t\t{{"if"
\t\t\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t\t\t{{var "enemyid$"}}
\t\t\t\t\t\t\t\t\t\t{{op "!="}}
\t\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{"if"
\t\t\t\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t\t\t\t{{var "id_1st_enemy$"}}
\t\t\t\t\t\t\t\t\t\t\t{{op "!="}}
\t\t\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{"if"
\t\t\t\t\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t\t\t\t\t{{var "id_defenderbot$"}}
\t\t\t\t\t\t\t\t\t\t\t\t{{op "!="}}
\t\t\t\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t\t\t\t{{var "cheat_enemyspawn$"}}
\t\t\t\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}"""
        fallback_checks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value 0}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"if"
\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t{{type entities}}
\t\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t\t{{player
\t\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t\t{{state operatable}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t\t{{state user_control}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_delete}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t\t{{state inactive}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t\t{{state dead}}
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
{inner_guard}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")

    switch_block = (
        f'\n\t\t\t\t\t{{"switch"\n{chr(10).join(conquest_cases)}\n\t\t\t\t\t}}'
        if is_dcg
        else ""
    )

    return f"""\t\t\t{{"cheats/auto_detect_player"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.cmp_i"
\t\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value 0}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 1.0}}
\t\t\t\t\t}}{switch_block}
{chr(10).join(fallback_checks)}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/auto_detect_player"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_options_player_trigger():
    """Cleanly cycles cheat_options-player$ AND syncs cheat_enemyspawn$, clearing old godmode/aimrange tags."""
    cases = []
    for p in range(8):
        nxt = (p + 1) % 8
        talk_idx = nxt - 1 if nxt in (1, 2, 3) else (3 if nxt == 0 else nxt)
        cases.append(f"""\t\t\t\t\t\t{{"case"
\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value {nxt}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_enemyspawn$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value {nxt}}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"talk"
\t\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t\t{{tag cheat_say}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{text "mission/singlecheats/c_setplayer_{talk_idx}"}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}""")
    return f"""\t\t\t{{"cheats/options/player"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/settings/player"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t{{var "cheat_player_detected$"}}
\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag cheat_godmode}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{impregnability disabled}}
\t\t\t\t\t\t{{tag_remove cheat_godmode}}
\t\t\t\t\t}}
\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag cheat_aimrange}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{tag_remove cheat_aimrange}}
\t\t\t\t\t}}
\t\t\t\t\t{{"switch"
{chr(10).join(cases)}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/settings/player"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/options/player"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_godmode_triggers():
    """Tag units given God Mode with cheat_godmode so toggling OFF or changing player clears EVERY buffed unit cleanly."""
    on_blocks = []
    for p in range(8):
        on_blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{player
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_godmode}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag "cheatsmod_inf-ammo"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state dead}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{impregnability full}}
\t\t\t\t\t\t\t{{tag_add cheat_godmode}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")

    god_on = f"""\t\t\t{{"cheats/active/godmodecheckon"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.cmp_i"
\t\t\t\t\t\t\t{{var "cheat_godmode$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 1}}
\t\t\t\t\t}}
{chr(10).join(on_blocks)}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/godmodecheckon"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""

    god_off = """\t\t\t{"cheats/active/godmodecheckoff"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"1.cmp_i"
\t\t\t\t\t\t\t{var "cheat_godmode$"}
\t\t\t\t\t\t\t{op "!="}
\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"delay"
\t\t\t\t\t\t{time 0.5}
\t\t\t\t\t}
\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{tag cheat_godmode}
\t\t\t\t\t\t}
\t\t\t\t\t\t{impregnability disabled}
\t\t\t\t\t\t{tag_remove cheat_godmode}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheats/active/godmodecheckoff"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""

    god_toggle = """\t\t\t{"cheats/godmode"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"1.event"
\t\t\t\t\t\t\t{id "cheats/godmode"}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"switch"
\t\t\t\t\t\t{"case"
\t\t\t\t\t\t\t{condition
\t\t\t\t\t\t\t\t{type cmp_i}
\t\t\t\t\t\t\t\t{var "cheat_godmode$"}
\t\t\t\t\t\t\t\t{op "=="}
\t\t\t\t\t\t\t\t{value 0}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"set_i"
\t\t\t\t\t\t\t\t{var "cheat_godmode$"}
\t\t\t\t\t\t\t\t{op "="}
\t\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"talk"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{tag cheat_say}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{text c_godmode_0}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\t{"case"
\t\t\t\t\t\t\t{condition
\t\t\t\t\t\t\t\t{type cmp_i}
\t\t\t\t\t\t\t\t{var "cheat_godmode$"}
\t\t\t\t\t\t\t\t{op "=="}
\t\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"set_i"
\t\t\t\t\t\t\t\t{var "cheat_godmode$"}
\t\t\t\t\t\t\t\t{op "="}
\t\t\t\t\t\t\t\t{value 0}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag cheat_godmode}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{impregnability disabled}
\t\t\t\t\t\t\t\t{tag_remove cheat_godmode}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"talk"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag cheat_say}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{text "mission/singlecheats/c_deactivated_0"}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\t{"event"
\t\t\t\t\t\t{event "cheats/godmode"}
\t\t\t\t\t\t{mode reset}
\t\t\t\t\t\t{delay 0}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheats/godmode"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""
    return god_on, god_off, god_toggle


def make_repair_trigger():
    """Repairs and refuels:
    1. All player, allied, captured/stolen, and neutral vehicles (excluding active enemy-crewed vehicles).
    2. All uninhabited vehicles and all hull-broken vehicle wrecks across the entire battlefield
       (excluding permanently destroyed burned-out hulks with destroyed_components 'body'), neutralizing
       any enemy-owned wreck to player '0' so friendly units don't shoot the newly repaired empty vehicle.
    """
    comps = [
        "turret",
        "aux_turret1",
        "aux_turret2",
        "aux_turret3",
        "aux_turret4",
        "mantlet",
        "gun",
        "gun1",
        "gun2",
        "gun3",
        "engine",
        "engine1",
        "engine2",
        "transmission",
        "trackleft",
        "trackright",
        "wheelleft",
        "wheelright",
        "wheelleft1",
        "wheelright1",
        "wheelleft2",
        "wheelright2",
        "wheelleft3",
        "wheelright3",
        "wheelleft4",
        "wheelright4",
        "cabin",
        "bodyback",
        "shield",
        "shield_cover",
        "fuel",
        "ammo",
        "body",
    ]
    tag_blocks = []
    neutralize_blocks = []
    for p in range(8):
        tag_blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{prop
\t\t\t\t\t\t\t\t\t\t\t{{prop vehicle}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{relation
\t\t\t\t\t\t\t\t\t\t\t{{relation enemy}}
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{destroyed_components
\t\t\t\t\t\t\t\t\t\t\t{{masks
\t\t\t\t\t\t\t\t\t\t\t\t"body"
\t\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state inactive}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{tag_add cheat_repair_target}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")
        neutralize_blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"player"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_repair_target}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{relation
\t\t\t\t\t\t\t\t\t\t\t{{relation enemy}}
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{operation set}}
\t\t\t\t\t\t\t{{player "0"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")

    wreck_tag_blocks = """\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t{prop vehicle}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state inhabited}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{destroyed_components
\t\t\t\t\t\t\t\t\t\t{masks
\t\t\t\t\t\t\t\t\t\t\t"body"
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state inactive}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag hidden}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\t{tag_add cheat_repair_target}
\t\t\t\t\t}
\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t{prop vehicle}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{broken_components
\t\t\t\t\t\t\t\t\t\t{masks
\t\t\t\t\t\t\t\t\t\t\t"body"
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{destroyed_components
\t\t\t\t\t\t\t\t\t\t{masks
\t\t\t\t\t\t\t\t\t\t\t"body"
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state inactive}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag hidden}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\t{tag_add cheat_repair_target}
\t\t\t\t\t}"""

    comp_cmds = []
    for c in comps:
        comp_cmds.append(f"""\t\t\t\t\t{{"actor_component"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag cheat_repair_target}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{component {c}}}
\t\t\t\t\t\t{{state work}}
\t\t\t\t\t}}""")

    return f"""\t\t\t{{"cheats/active/repair"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheat_repair"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{chr(10).join(tag_blocks)}
{wreck_tag_blocks}
{chr(10).join(neutralize_blocks)}
{chr(10).join(comp_cmds)}
\t\t\t\t\t{{"inventory"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag cheat_repair_target}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{action fuel}}
\t\t\t\t\t\t{{amount 999}}
\t\t\t\t\t}}
\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag cheat_repair_target}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{tag_remove cheat_repair_target}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheat_repair"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/repair"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_destroyarmor_trigger():
    comps = ["gun", "turret", "engine", "trackleft", "trackright"]
    blocks = []
    for p in range(8):
        comp_cmds = []
        for c in comps:
            comp_cmds.append(f"""\t\t\t\t\t\t{{"actor_component"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{relation
\t\t\t\t\t\t\t\t\t\t\t{{relation enemy}}
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{prop
\t\t\t\t\t\t\t\t\t\t\t{{prop vehicle}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{component {c}}}
\t\t\t\t\t\t\t{{state broken}}
\t\t\t\t\t\t}}""")
        blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
{chr(10).join(comp_cmds)}
\t\t\t\t\t}}""")
    return f"""\t\t\t{{"cheats/destroyarmor"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/destroyarmor"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{chr(10).join(blocks)}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/destroyarmor"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/destroyarmor"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_aimrange_trigger():
    # Tag ONLY the selected cheat_options-player$ slot so AI bots in Conquest/Skirmish NEVER receive Range & Accuracy!
    blocks = []
    for p in range(8):
        blocks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{player
\t\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_aimrange}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state dead}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag hidden}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{tag_add cheat_aimrange}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")
    return f"""\t\t\t{{"cheats/active/aimrange"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.cmp_i"
\t\t\t\t\t\t\t{{var "cheat_aimrange$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 1}}
\t\t\t\t\t}}
{chr(10).join(blocks)}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/aimrange"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_aimrange_off_trigger():
    return """\t\t\t{"cheats/active/aimrange_off"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"1.cmp_i"
\t\t\t\t\t\t\t{var "cheat_aimrange$"}
\t\t\t\t\t\t\t{op "!="}
\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"delay"
\t\t\t\t\t\t{time 0.5}
\t\t\t\t\t}
\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t\t\t}
\t\t\t\t\t\t{tag_remove cheat_aimrange}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheats/active/aimrange_off"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""


def make_miner_trigger():
    # Uses pre-placed hidden template 0x8000 (tag: cheat_infantry-ger1, cheat_infantry_spawn, hidden).
    # Cloned units do not carry the hidden tag, so excluding {tag hidden} targets only the new clone!
    sel_clone = """\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{select
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag cheat_infantry_spawn}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag hidden}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}"""
    player_assign = []
    for p in range(8):
        player_assign.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"player"
{sel_clone.replace(chr(9)*6, chr(9)*7)}
\t\t\t\t\t\t\t{{operation set}}
\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")
    return f"""\t\t\t{{"cheats/units/fast_miner"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/fast_miner"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"actor_to_waypoint"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{tag "cheat_infantry-ger1"}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{waypoint "7901"}}
\t\t\t\t\t\t{{clone}}
\t\t\t\t\t\t{{approach teleport}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
{sel_clone}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine m1a1_cheat"}}
\t\t\t\t\t\t{{amount 40}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
{sel_clone}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine s_cheat"}}
\t\t\t\t\t\t{{amount 40}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
{sel_clone}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine_detector"}}
\t\t\t\t\t\t{{amount 1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"actor_state"
{sel_clone}
\t\t\t\t\t\t{{control user}}
\t\t\t\t\t\t{{human
\t\t\t\t\t\t\t{{veterancy 8}}
\t\t\t\t\t\t\t{{stamina 100}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
{chr(10).join(player_assign)}
\t\t\t\t\t{{"entity_state"
{sel_clone}
\t\t\t\t\t\t{{tag_add cheat_delete}}
\t\t\t\t\t\t{{tag_remove cheat_infantry_spawn}}
\t\t\t\t\t\t{{tag_remove "cheat_infantry-ger1"}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/fast_miner"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/units/fast_miner"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_conquest_win_trigger(is_dcg=False):
    win_action = (
        '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "gameover_request_player_win$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 1}\n\t\t\t\t\t}'
        if is_dcg
        else '\t\t\t\t\t{"gameover"\n\t\t\t\t\t\t{result win}\n\t\t\t\t\t\t{message "$/complete"}\n\t\t\t\t\t}'
    )
    return f"""\t\t\t{{"cheats/active/conquest_win"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/conquest_win"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{win_action}
\t\t\t\t\t{{"sound"
\t\t\t\t\t\t{{name "mission/task_fulfilled"}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/conquest_win"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/conquest_win"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_money_trigger():
    return """\t\t\t{"cheats/money"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"1.event"
\t\t\t\t\t\t\t{id "cheat_money"}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t{operation score_total}
\t\t\t\t\t\t{score 99999}
\t\t\t\t\t}
\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t{operation score_add}
\t\t\t\t\t\t{score 1000}
\t\t\t\t\t}
\t\t\t\t\t{"event"
\t\t\t\t\t\t{event "cheat_money"}
\t\t\t\t\t\t{mode reset}
\t\t\t\t\t\t{delay 0}
\t\t\t\t\t}
\t\t\t\t\t{"delay"
\t\t\t\t\t\t{time 0.1}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheats/money"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""


def write_conquest_budget_files():
    """Read vanilla v1.069.0 resources_*.set from gamelogic.pak and boost only {Budget} to 2000 CP + 2.0/s."""
    gl_pak = os.path.join(GOH_DIR, "resource", "gamelogic.pak")
    out_dc = os.path.join(MOD, "resource", "set", "dynamic_campaign")
    os.makedirs(out_dc, exist_ok=True)

    def patch_budget_block(m):
        blk = m.group(0)
        blk, n1 = re.subn(
            r'\{Start\s+"[^"]+"\}',
            '{Start "0:2000 4:2000 8:2000 12:2000 16:2000 20:2000"}',
            blk,
        )
        blk, n2 = re.subn(r'\{PointsPerSecond\s+[0-9.]+\}', '{PointsPerSecond 2.0}', blk)
        blk, n3 = re.subn(r'\{Limit\s+\d+\}', '{Limit 2000}', blk)
        assert n1 == 1 and n2 == 1 and n3 == 1, f"Unexpected Budget block fields: {n1},{n2},{n3}"
        return blk

    with zipfile.ZipFile(gl_pak, "r") as zgl:
        for fname in ("resources_low.set", "resources_standard.set", "resources_high.set", "resources_very_high.set"):
            txt = zgl.read(f"set/dynamic_campaign/{fname}").decode("utf-8", errors="replace").replace("\r\n", "\n")
            assert re.search(r"\{PaybackFactor\s+[0-9.]+\s+0\s+0\s+0\}", txt), f"Missing v1.069.0 PaybackFactor 4-tuple in {fname}"
            txt, nb = re.subn(r'\{Budget\b.*?\n\t\t\}', patch_budget_block, txt, flags=re.S)
            assert nb == 1, f"Expected 1 {{Budget}} block in {fname}, got {nb}"
            assert '{Start "0:2000 4:2000 8:2000 12:2000 16:2000 20:2000"}' in txt
            assert "{PointsPerSecond 2.0}" in txt
            assert "{Limit 2000}" in txt
            with open(os.path.join(out_dc, fname), "w", encoding="utf-8", newline="") as f:
                f.write(txt.replace("\n", "\r\n"))
    print("Wrote vanilla v1.069.0-based 2000-CP Conquest Budget resources_*.set files.")


def replace_trigger_block(txt, trigger_header, new_block):
    """Replace an entire top-level trigger block starting with trigger_header (e.g. '\t\t\t{"cheats/active/addexp"')."""
    lines = txt.splitlines()
    start_idx = None
    for i, l in enumerate(lines):
        if l.strip() == trigger_header.strip():
            start_idx = i
            break
    if start_idx is None:
        return txt, False
    depth = 0
    end_idx = start_idx
    for j in range(start_idx, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if j > start_idx and depth <= 0:
            end_idx = j
            break
    repl = new_block.splitlines() if new_block else []
    new_lines = lines[:start_idx] + repl + lines[end_idx + 1 :]
    return "\n".join(new_lines), True


def generate_custom_button_icons():
    """Generate authentic 104x52 3-state (_00, _01, _02) TGA button icons in interface.pak from native game assets."""
    iface_pak = os.path.join(MOD, "resource", "interface.pak")
    tmp_pak = iface_pak + ".tmp"
    goh_res_if = os.path.join(GOH_DIR, "resource", "interface")

    def load_img(z, path):
        return Image.open(io.BytesIO(z.read(path))).convert("RGBA")

    def build_clean_plate(zin, state, is_submenu=False):
        s = load_img(zin, f"interface/scene/unit_icon/whitesnoop/infantry/single_{state}.tga")
        m = load_img(zin, f"interface/scene/unit_icon/whitesnoop/cheats/money_{state}.tga")
        mi = load_img(zin, f"interface/scene/unit_icon/whitesnoop/menus/menu_item_{state}.tga")
        out = m.copy()
        src_l = s.crop((6, 17, 34, 48))
        src_r = s.crop((58, 17, 84, 48))
        fill = Image.new("RGBA", (66, 31))
        fill.paste(src_l, (0, 0))
        fill.paste(src_r, (28, 0))
        fill.paste(src_r.crop((0, 0, 12, 31)).transpose(Image.Transpose.FLIP_LEFT_RIGHT), (54, 0))
        mask = Image.new("L", (66, 31), 255)
        mp = mask.load()
        for x in range(6):
            a = int(255 * (0.5 - 0.5 * math.cos(math.pi * x / 6.0)))
            for y in range(31):
                mp[x, y] = a
                mp[65 - x, y] = a
        out.paste(fill, (18, 17), mask)
        if is_submenu:
            out.paste(mi.crop((85, 0, 104, 52)), (85, 0))
        return out

    def diff_cutout(target_im, bg_im, thresh=18):
        t = target_im.copy()
        w, h = t.size
        tp = t.load()
        bp = bg_im.load()
        for y in range(h):
            for x in range(w):
                if x < 5 or x > 84 or y < 15 or y > 48:
                    tp[x, y] = (0, 0, 0, 0)
                    continue
                r1, g1, b1, _ = tp[x, y]
                r2, g2, b2, _ = bp[x, y]
                diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
                a = 0 if diff < thresh else min(255, int((diff - thresh) * 5))
                tp[x, y] = (r1, g1, b1, a)
        bbox = t.getbbox()
        return t.crop(bbox) if bbox else t

    def tint_rgba(im, rgb):
        out = im.copy()
        px = out.load()
        for y in range(out.height):
            for x in range(out.width):
                r, g, b, a = px[x, y]
                lum = (r * 0.3 + g * 0.59 + b * 0.11) / 255.0
                px[x, y] = (
                    min(255, int(rgb[0] * (0.4 + 0.6 * lum))),
                    min(255, int(rgb[1] * (0.4 + 0.6 * lum))),
                    min(255, int(rgb[2] * (0.4 + 0.6 * lum))),
                    a,
                )
        return out

    def remove_dark_bg(im, thresh=68, fade=30):
        out = im.copy()
        px = out.load()
        for y in range(out.height):
            for x in range(out.width):
                r, g, b, a = px[x, y]
                mx = max(r, g, b)
                sat = mx - min(r, g, b)
                score = mx + sat * 0.5
                if score < thresh:
                    px[x, y] = (r, g, b, 0)
                elif score < thresh + fade:
                    px[x, y] = (r, g, b, int(a * (score - thresh) / fade))
        bbox = out.getbbox()
        return out.crop(bbox) if bbox else out

    def composite_centered(plate, icon, cx, cy, max_h=28, max_w=54, sh_alpha=155):
        ic = icon.copy()
        bbox = ic.getbbox()
        if bbox:
            ic = ic.crop(bbox)
        scale = min(max_w / ic.width, max_h / ic.height)
        nw = max(1, int(round(ic.width * scale)))
        nh = max(1, int(round(ic.height * scale)))
        ic = ic.resize((nw, nh), Image.Resampling.LANCZOS)
        sh = Image.new("RGBA", (nw + 8, nh + 8), (0, 0, 0, 0))
        al = ic.split()[3].point(lambda a: int(a * sh_alpha / 255))
        sh.paste((8, 8, 6, 255), (4, 4), al)
        sh = sh.filter(ImageFilter.GaussianBlur(1.2))
        out = plate.copy()
        out.alpha_composite(sh, (cx - nw // 2 - 3, cy - nh // 2 - 2))
        out.alpha_composite(ic, (cx - nw // 2, cy - nh // 2))
        return out

    def adjust_state(im, state):
        if state == "01":
            return ImageEnhance.Brightness(im).enhance(1.12)
        if state == "02":
            return ImageEnhance.Brightness(im).enhance(0.88)
        return im

    with (
        zipfile.ZipFile(iface_pak, "r") as zin,
        zipfile.ZipFile(tmp_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout,
        zipfile.ZipFile(os.path.join(goh_res_if, "scene.pak"), "r") as z_scene,
        zipfile.ZipFile(os.path.join(goh_res_if, "pages.pak"), "r") as z_pages,
        zipfile.ZipFile(os.path.join(goh_res_if, "interface.pak"), "r") as z_goh_if,
    ):
        plates = {}
        for state in ("00", "01", "02"):
            plates[(state, False)] = build_clean_plate(zin, state, is_submenu=False)
            plates[(state, True)] = build_clean_plate(zin, state, is_submenu=True)

        b0 = plates[("00", False)]
        wrench = load_img(z_goh_if, "cursor/repair/00.tga")
        xhair_pure = load_img(z_scene, "scene/minimap/crosshair_00.tga")
        xhair_red = tint_rgba(xhair_pure, (235, 55, 45))
        xhair_gold = tint_rgba(xhair_pure, (240, 200, 95))
        star = load_img(z_pages, "pages/main/star_active.tga")
        medal = load_img(z_pages, "pages/inventory/medals/ww2_veteran_medal_small.dds")
        rank8_clean = remove_dark_bg(
            load_img(z_pages, "pages/main/dynamic_campaign/icon_rank8.tga").crop((3, 3, 38, 25)),
            thresh=68,
            fade=30,
        )
        rank8_clean = ImageEnhance.Contrast(ImageEnhance.Brightness(rank8_clean).enhance(1.3)).enhance(1.2)
        gear = load_img(z_goh_if, "skin/game/button/bkg/menu_options_00.tga")
        heavy_sil = diff_cutout(load_img(zin, "interface/scene/unit_icon/whitesnoop/menus/vehicle_class/heavy_00.tga"), b0, thresh=22)
        mines_cut = diff_cutout(load_img(zin, "interface/scene/unit_icon/whitesnoop/cheats/mines_00.tga"), b0, thresh=24)
        veh_cut = diff_cutout(load_img(zin, "interface/scene/unit_icon/whitesnoop/menus/vehicle_00.tga"), b0, thresh=18)
        arty_cut = diff_cutout(load_img(zin, "interface/scene/unit_icon/whitesnoop/menus/arty_00.tga"), b0, thresh=18)

        da_comp = Image.new("RGBA", (62, 32), (0, 0, 0, 0))
        da_comp.alpha_composite(heavy_sil.resize((52, 20), Image.Resampling.LANCZOS), (5, 7))
        da_comp.alpha_composite(xhair_red.resize((26, 26), Image.Resampling.LANCZOS), (18, 3))

        fm_comp = Image.new("RGBA", (66, 34), (0, 0, 0, 0))
        mc_s = mines_cut.copy()
        mc_s.thumbnail((42, 28), Image.Resampling.LANCZOS)
        fm_comp.alpha_composite(mc_s, (1, 4))
        fm_comp.alpha_composite(wrench.resize((22, 22), Image.Resampling.LANCZOS), (42, 4))

        sup_comp = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
        ac_s = arty_cut.copy()
        ac_s.thumbnail((44, 27), Image.Resampling.LANCZOS)
        sup_comp.alpha_composite(ac_s, (1, 3))
        sup_comp.alpha_composite(xhair_gold.resize((20, 20), Image.Resampling.LANCZOS), (42, 5))

        manual_ctrl = load_img(z_scene, "scene/panel_control/manual_control_00.tga")
        move_raw = load_img(z_scene, "scene/panel_control/move_00.tga").crop((13, 13, 51, 51))
        mpx = move_raw.load()
        for my in range(move_raw.height):
            for mx in range(move_raw.width):
                mr, mg, mb, _ = mpx[mx, my]
                mlum = 0.3 * mr + 0.59 * mg + 0.11 * mb
                if mlum < 92:
                    mpx[mx, my] = (mr, mg, mb, 0)
                else:
                    ma = min(255, int((mlum - 92) * 5.5))
                    mpx[mx, my] = (min(255, int(mr * 1.2)), min(255, int(mg * 1.2)), min(255, int(mb * 1.2)), ma)
        if move_raw.getbbox():
            move_raw = move_raw.crop(move_raw.getbbox())
        gear_tight = gear.crop(gear.getbbox()) if gear.getbbox() else gear
        ai_comp = Image.new("RGBA", (62, 34), (0, 0, 0, 0))
        ai_sol = tint_rgba(move_raw, (238, 224, 195))
        ai_sol.thumbnail((32, 32), Image.Resampling.LANCZOS)
        ai_gear = tint_rgba(gear_tight, (240, 175, 65))
        ai_gear.thumbnail((24, 24), Image.Resampling.LANCZOS)
        ai_comp.alpha_composite(ai_sol, (4, 1))
        ai_comp.alpha_composite(ai_gear, (34, 5))

        icon_specs = {
            "repair": (False, wrench, 52, 33, 28, 46),
            "destroyarmor": (False, da_comp, 52, 33, 30, 62),
            "veterancy": (False, rank8_clean, 52, 33, 27, 56),
            "win": (False, medal, 52, 33, 28, 34),
            "fastminer": (False, fm_comp, 52, 33, 30, 66),
            "control_user": (False, manual_ctrl, 52, 33, 28, 36),
            "control_ai": (False, ai_comp, 52, 33, 29, 58),
            "menu_spawn": (True, veh_cut, 44, 33, 29, 58),
            "menu_cheats": (True, star, 45, 33, 29, 44),
            "menu_settings": (True, gear, 45, 33, 26, 36),
            "menu_support": (True, sup_comp, 45, 33, 29, 64),
        }

        generated_names = {
            f"interface/scene/unit_icon/whitesnoop/cheats/{name}_{st}.tga".lower()
            for name in icon_specs
            for st in ("00", "01", "02")
        }

        for item in zin.infolist():
            if item.filename.lower() in generated_names:
                continue
            zout.writestr(item, zin.read(item.filename))

        for icon_name, (is_sub, asset, cx, cy, mh, mw) in icon_specs.items():
            for state in ("00", "01", "02"):
                im = composite_centered(plates[(state, is_sub)], adjust_state(asset, state), cx, cy, max_h=mh, max_w=mw)
                buf = io.BytesIO()
                im.save(buf, format="TGA")
                out_name = f"interface/scene/unit_icon/whitesnoop/cheats/{icon_name}_{state}.tga"
                zout.writestr(out_name, buf.getvalue())

    os.replace(tmp_pak, iface_pak)
    print(f"Generated {len(icon_specs)} native-style 3-state TGA button icons in interface.pak.")


def patch_mi_content(raw_txt, label, is_dcg=False):
    txt = raw_txt.replace("\r\n", "\n")

    # 0. Remap out-of-bounds 30000..30007 waypoints to safe 7900..7907 inside GEM2's 8192-bit waypoint bitmap
    for old_wp, new_wp in (
        ("30000", "7900"),
        ("30001", "7901"),
        ("30002", "7902"),
        ("30005", "7905"),
        ("30006", "7906"),
        ("30007", "7907"),
    ):
        txt = txt.replace(f'"{old_wp}"', f'"{new_wp}"')

    # 1. Strip all Chinese text from button labels
    cn_replacements = [
        ('{text "Cheat Ammo Box   无限弹药箱"}', '{text "Cheat Ammo Box"}'),
        ('{text "Health & Armour   无敌"}', '{text "God Mode"}'),
        ('{text "Infinite Ammo  无限子弹"}', '{text "Infinite Ammo"}'),
        ('{text "Fuel & Stamina  无限体力/油"}', '{text "Fuel & Stamina"}'),
        ('{text "Aimrange  无限射程"}', '{text "Range & Accuracy"}'),
        ('{text "Instakill  秒杀"}', '{text "Instakill"}'),
        ('{text "Full Level Soldier 满级士兵"}', '{text "Max Veterancy"}'),
    ]
    for old, new in cn_replacements:
        txt = txt.replace(old, new)

    # 2. Register new events & vars ("cheats/fast_miner", "cheats/conquest_win", "cheat_player_detected")
    if '{"cheat_player_detected"}' not in txt:
        txt = txt.replace('{"cheat_options-player"}', '{"cheat_options-player"}\n\t\t\t{"cheat_player_detected"}', 1)
    if '{event "cheats/fast_miner"}' not in txt:
        txt = txt.replace('{event "cheat_delete"}', '{event "cheat_delete"}\n\t\t{event "cheats/fast_miner"}\n\t\t{event "cheats/conquest_win"}', 1)

    # 3. Fix cheat_destroyarmor {count 0} -> {count -1} and add clean text
    txt = re.sub(
        r'(\{"cheat_destroyarmor"\n\t\t\t\t\{state hidden\}\n\t\t\t\t\{text )""(\}\n\t\t\t\t\{image "whitesnoop/cheats/destroyarmor"\}\n\t\t\t\t\{hint "mission/singlecheats/Destroy enemy armor"\}\n\t\t\t\t\{count )0(\})',
        r'\1"Destroy Enemy Armor"\2-1\3',
        txt,
    )

    # 3b. Add cheat_conquest_win reinforcement button right after cheat_repair
    if '{"cheat_conquest_win"' not in txt:
        win_btn = """\t\t\t{"cheat_conquest_win"
\t\t\t\t{state hidden}
\t\t\t\t{text "Instant Win"}
\t\t\t\t{image "whitesnoop/cheats/win"}
\t\t\t\t{hint "Immediately win the current Conquest battle with full victory rewards"}
\t\t\t\t{count -1}
\t\t\t\t{score 0}
\t\t\t\t{delay 0}
\t\t\t\t{eventStart "cheat_click"}
\t\t\t\t{eventEnd "cheats/conquest_win"}
\t\t\t}"""
        txt = txt.replace(
            '\t\t\t{"cheat_repair"\n',
            win_btn + '\n\t\t\t{"cheat_repair"\n',
            1,
        )

    # 4. Add cheat_miner reinforcement button right before cheat_mine
    if '{"cheat_miner"' not in txt:
        miner_btn = """\t\t\t{"cheat_miner"
\t\t\t\t{state hidden}
\t\t\t\t{text "Fast Mine Engineer"}
\t\t\t\t{image "whitesnoop/cheats/fastminer"}
\t\t\t\t{hint "Click on ground to spawn Engineer with 40 AT + 40 AP instant (0.1s) mines. Hold Shift to queue!"}
\t\t\t\t{count -1}
\t\t\t\t{score 0}
\t\t\t\t{delay 0}
\t\t\t\t{eventStart "cheat_click"}
\t\t\t\t{eventEnd "cheats/fast_miner"}
\t\t\t\t{waypoint "7901"}
\t\t\t}"""
        txt = txt.replace(
            '\t\t\t{"cheat_mine"\n',
            miner_btn + '\n\t\t\t{"cheat_mine"\n',
            1,
        )

    # 4b. Polish all button icons, titles, and tooltips (runs AFTER inserting new buttons!)
    button_updates = {
        "cheats": ('"CheatsMod"', '"whitesnoop/menus/whitesnewps"', '"Open CheatsMod 2.6 Reworked menu (Spawn Units, Cheats, Settings)"'),
        "cheatmenu_1": ('"Spawn Units"', '"whitesnoop/cheats/menu_spawn"', '"Spawn infantry, squads, BTRs, tanks, artillery, aircraft, or support tools"'),
        "cheatmenu_2": ('"Cheats"', '"whitesnoop/cheats/menu_cheats"', '"Combat cheats: God Mode, Infinite Ammo, Range, Instakill, Max Veterancy, Repairs, Instant Win"'),
        "cheatmenu_3": ('"Settings"', '"whitesnoop/cheats/menu_settings"', '"Player slot override (0-7) and aircraft spawn altitude"'),
        "cheatspawnmenu_support": ('"Support"', '"whitesnoop/cheats/menu_support"', '"Ammo Boxes, Fast Mine Engineer, AT/AP Mines, Artillery, Mortar & Clear Cheated"'),
        "cheatspawnmenu_infantry": ('"Infantry"', None, '"Spawn single soldiers or full infantry squads"'),
        "cheatspawnmenu_vehicles": ('"Tanks & Vehicles"', None, '"Spawn BTRs, light, medium, or heavy tanks"'),
        "cheatspawnmenu_artillery": ('"Artillery"', None, '"Spawn towed artillery & AT/AA guns"'),
        "cheatspawnmenu_airplanes": ('"Aircraft"', None, '"Call in aircraft flyovers / air support"'),
        "cheatspawnmenu_mod_vehicles": ('"Mod Units"', None, '"Spawn custom mod vehicles & infantry configured via *_list.txt"'),
        "cheat_addmoney": ('"+1000 SP Points"', None, '"Singleplayer & SP Skirmish only: add +1000 Reinforcement Score (Conquest already starts with 2000 CP call-in budget; Multiplayer MP is lobby-controlled)"'),
        "cheat_godmode_off": ('"God Mode"', None, '"Enable: make all your units and vehicles invulnerable"'),
        "cheat_godmode_on": ('"God Mode"', None, '"Disable: turn off God Mode"'),
        "cheat_infammo_off": ('"Infinite Ammo"', None, '"Enable: spawn a map-wide (500m) resupply aura refilling ammo & fuel"'),
        "cheat_infammo_on": ('"Infinite Ammo"', None, '"Disable: remove map-wide resupply aura"'),
        "cheat_fuel-stam-off": ('"Fuel & Stamina"', None, '"Enable: keep soldier stamina at 100% and vehicle fuel full"'),
        "cheat_fuel-stam-on": ('"Fuel & Stamina"', None, '"Disable: turn off infinite fuel & stamina"'),
        "cheat_aimrange_accuracy_on": ('"Range & Accuracy"', None, '"Enable: massively extend weapon range and grant pinpoint mortar & gun accuracy"'),
        "cheat_aimrange_accuracy_off": ('"Range & Accuracy"', None, '"Disable: restore normal weapon range and accuracy"'),
        "cheat_enemy": ('"Enemy Cheats"', None, '"Cheats below target enemy units on the map"'),
        "cheatweakenemy": ('"Instakill"', None, '"Enable: reduce enemy soldier HP to 1 and enemy vehicle armor to 1%"'),
        "cheatweakenemyoff": ('"Instakill"', None, '"Disable: restore normal enemy HP and armor"'),
        "cheat_addexp": ('"Max Veterancy"', '"whitesnoop/cheats/veterancy"', '"One-shot: promote all currently alive friendly infantry, gun crews, and vehicle crews to Level 8"'),
        "cheat_conquest_win": ('"Instant Win"', '"whitesnoop/cheats/win"', '"Immediately win the current battle (Conquest victory with full rewards, or Singleplayer mission win)"'),
        "cheat_repair": ('"Repair Vehicles"', '"whitesnoop/cheats/repair"', '"Instantly repair & refuel all your vehicles, captured/stolen enemy vehicles, and all repairable battlefield wrecks"'),
        "cheat_destroyarmor": ('"Break Enemy Armor"', '"whitesnoop/cheats/destroyarmor"', '"Break gun, turret, engine & tracks on all enemy vehicles on the map"'),
        "cheat_explosion": ('"Explosion"', None, '"Click on the ground to trigger an explosion at cursor"'),
        "cheat_artillery": ('"Artillery Barrage"', None, '"Click on the ground to call an artillery barrage at cursor"'),
        "cheat_mortar": ('"Mortar Barrage"', None, '"Click on the ground to call a mortar barrage at cursor"'),
        "cheat_miner": ('"Fast Mine Engineer"', '"whitesnoop/cheats/fastminer"', '"Click on ground to spawn Engineer with 40 AT + 40 AP instant (0.1s) mines. Hold Shift to queue!"'),
        "cheat_mine": ('"AT Mines (x8)"', None, '"Click on the ground to drop 8 armed Anti-Tank mines"'),
        "cheat_mine_ap": ('"AP Mines (x8)"', None, '"Click on the ground to drop 8 armed Anti-Personnel mines"'),
        "cheat_ammo": ('"Ammo Box"', None, '"Click on ground to deploy an FPS-friendly resupply crate (all factions + MACE)"'),
        "cheat_ammodrop": ('"Paradrop Ammo"', None, '"Click on the ground to paradrop a supply crate at cursor"'),
        "cheat_delete": ('"Clear Cheated"', None, '"Delete all units & objects spawned by CheatsMod from the map"'),
        "cheat_return": ('"Back"', None, '"Return to previous menu"'),
        "changecn_user": ('"Control: Manual"', '"whitesnoop/cheats/control_user"', '"Spawned units are under your manual control (click to switch to autonomous AI)"'),
        "changecn_ai": ('"Control: AI"', '"whitesnoop/cheats/control_ai"', '"Spawned units move and fight autonomously under AI control (click to switch to Manual)"'),
        "cheat_options-planeheight1": ('"Plane Height: 15m"', None, '"Aircraft spawn altitude: 15m (click to cycle 15m / 20m / 25m)"'),
        "cheat_options-planeheight2": ('"Plane Height: 20m"', None, '"Aircraft spawn altitude: 20m (click to cycle 15m / 20m / 25m)"'),
        "cheat_options-planeheight3": ('"Plane Height: 25m"', None, '"Aircraft spawn altitude: 25m (click to cycle 15m / 20m / 25m)"'),
        "cheat_air1": ('"[Ger] Bf 109 G-6"', None, '"Click on ground to spawn a German Bf 109 G-6 aircraft"'),
        "cheat_air2": ('"[Ger] Bf 110 E-2"', None, '"Click on ground to spawn a German Bf 110 E-2 aircraft"'),
        "cheat_air3": ('"[Ger] Fi 156"', None, '"Click on ground to spawn a German Fi 156 recon plane"'),
        "cheat_air4": ('"[Rus] Yak-1"', None, '"Click on ground to spawn a Soviet Yak-1 aircraft"'),
        "cheat_air5": ('"[Rus] IL-2"', None, '"Click on ground to spawn a Soviet IL-2 attack aircraft"'),
        "cheat_air6": ('"[Rus] Po-2"', None, '"Click on ground to spawn a Soviet Po-2 biplane"'),
        "cheat_air7": ('"[Usa] P-47D-22"', None, '"Click on ground to spawn a US P-47D-22 aircraft"'),
        "cheat_air8": ('"[Eng] Blenheim Mk.I"', None, '"Click on ground to spawn a British Blenheim Mk.I bomber"'),
        "changecountry_ger": ('""', None, '"Switch spawn roster to Germany"'),
        "changecountry_usa": ('""', None, '"Switch spawn roster to USA"'),
        "changecountry_uk": ('""', None, '"Switch spawn roster to Finland / Commonwealth"'),
        "changecountry_rus": ('""', None, '"Switch spawn roster to USSR"'),
        "changecountry_jap": ('""', None, '"Switch spawn roster to Other / Special"'),
    }
    for slot_idx in range(1, 9):
        p_num = slot_idx if slot_idx < 8 else 0
        nxt_num = (p_num + 1) % 8
        button_updates[f"cheat_spawnasplayer{slot_idx}"] = (
            None,
            None,
            f'"Spawned units belong to Player {p_num} (auto-detected; click to switch to Player {nxt_num})"',
        )
        button_updates[f"cheat_options-player{slot_idx}"] = (
            None,
            None,
            f'"Cheats & spawns target Player {p_num} (auto-detected; click to switch to Player {nxt_num})"',
        )

    for btn_id, (new_text, new_img, new_hint) in button_updates.items():
        bpat = re.compile(
            r'(\t\t\t\{"' + re.escape(btn_id) + r'"\n\t\t\t\t\{state hidden\}\n)(\t\t\t\t\{text [^\n]+\}\n)(\t\t\t\t\{image [^\n]+\}\n)\t\t\t\t\{hint [^\n]+\}\n'
        )
        m = bpat.search(txt)
        if m:
            txt_line = f'\t\t\t\t{{text {new_text}}}\n' if new_text is not None else m.group(2)
            img_line = f'\t\t\t\t{{image {new_img}}}\n' if new_img else m.group(3)
            rep = f'{m.group(1)}{txt_line}{img_line}\t\t\t\t{{hint {new_hint}}}\n'
            txt = txt[:m.start()] + rep + txt[m.end():]

    # 5. Show & hide cheat_miner in Support menu (20:supportcheats)
    if "{name cheat_miner}" not in txt:
        txt = txt.replace(
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_mine}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_miner}\n\t\t\t\t\t}\n\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_mine}\n\t\t\t\t\t}',
        )
        txt = txt.replace(
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_mine}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_miner}\n\t\t\t\t\t}\n\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_mine}\n\t\t\t\t\t}',
        )

    # 6. Show cheat_repair & cheat_conquest_win in cheat_menu/show/99:cheats + hide in 99:cheats + fix swapped aimrange icons!
    if "{name cheat_conquest_win}" not in txt:
        txt = txt.replace(
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_addexp}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_addexp}\n\t\t\t\t\t}\n\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_repair}\n\t\t\t\t\t}\n\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation show}\n\t\t\t\t\t\t{name cheat_conquest_win}\n\t\t\t\t\t}',
        )
        txt = txt.replace(
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_addexp}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_addexp}\n\t\t\t\t\t}\n\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name cheat_conquest_win}\n\t\t\t\t\t}',
        )

    # Normalize aimrange toggle icons: _on has image "disabled" (shown when != 1), _off has image "enabled" (shown when == 1)
    correct_aim_show = """\t\t\t\t\t{"if"
\t\t\t\t\t\t{condition
\t\t\t\t\t\t\t{type cmp_i}
\t\t\t\t\t\t\t{var "cheat_aimrange$"}
\t\t\t\t\t\t\t{op "!="}
\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t}
\t\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t\t{operation show}
\t\t\t\t\t\t\t{name cheat_aimrange_accuracy_on}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\t{"if"
\t\t\t\t\t\t{condition
\t\t\t\t\t\t\t{type cmp_i}
\t\t\t\t\t\t\t{var "cheat_aimrange$"}
\t\t\t\t\t\t\t{op "=="}
\t\t\t\t\t\t\t{value 1}
\t\t\t\t\t\t}
\t\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t\t{operation show}
\t\t\t\t\t\t\t{name cheat_aimrange_accuracy_off}
\t\t\t\t\t\t}
\t\t\t\t\t}"""
    swapped_aim_show = correct_aim_show.replace("cheat_aimrange_accuracy_on", "__TMP__").replace("cheat_aimrange_accuracy_off", "cheat_aimrange_accuracy_on").replace("__TMP__", "cheat_aimrange_accuracy_off")
    if swapped_aim_show in txt:
        txt = txt.replace(swapped_aim_show, correct_aim_show, 1)
    assert correct_aim_show in txt, f"Failed to verify normalized aimrange show block in {label}"

    # 7. Initialize cheat_options-player$ = 0 and explicitly reset one-shot events in cheats/set/vars idempotently
    vars_anchor = '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_infammo$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}'
    old_vars_init_blk = (
        '\n\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_options-player$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_player_detected$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/addexp"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/conquest_win"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheat_repair"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/destroyarmor"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
        '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/fast_miner"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
    )
    vars_init_blk = (
        old_vars_init_blk
        + '\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheat_money"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}'
    )
    txt = txt.replace(vars_init_blk, "").replace(old_vars_init_blk, "")
    assert vars_anchor in txt, f"cheats/set/vars anchor not found in {label}"
    txt = txt.replace(vars_anchor, vars_anchor + vars_init_blk, 1)

    # 8. Replace broken triggers idempotently + add auto_detect_player + conquest_win + fast_miner + money
    for dup_hdr in ('{"cheats/auto_detect_player"', '{"cheats/active/repair"', '{"cheats/active/conquest_win"', '{"cheats/units/fast_miner"'):
        txt, _ = replace_trigger_block(txt, dup_hdr, "")
    txt, ok1 = replace_trigger_block(
        txt,
        '{"cheats/active/addexp"',
        make_auto_detect_player_trigger(is_dcg=is_dcg)
        + "\n"
        + make_addexp_trigger()
        + "\n"
        + make_repair_trigger()
        + "\n"
        + make_conquest_win_trigger(is_dcg=is_dcg)
        + "\n"
        + make_miner_trigger(),
    )
    txt, ok_mon = replace_trigger_block(txt, '{"cheats/money"', make_money_trigger())
    assert ok_mon, f"cheats/money replace failed in {label}"
    txt, ok2 = replace_trigger_block(txt, '{## "cheats/destroyarmor"', make_destroyarmor_trigger())
    if not ok2:
        txt, ok2 = replace_trigger_block(txt, '{"cheats/destroyarmor"', make_destroyarmor_trigger())
    txt, ok3 = replace_trigger_block(txt, '{"cheats/active/aimrange"', make_aimrange_trigger())
    txt, _ = replace_trigger_block(txt, '{"cheats/active/aimrange_off"', make_aimrange_off_trigger())
    god_on, god_off, god_toggle = make_godmode_triggers()
    txt, ok_gon = replace_trigger_block(txt, '{"cheats/active/godmodecheckon"', god_on)
    txt, ok_goff = replace_trigger_block(txt, '{"cheats/active/godmodecheckoff"', god_off)
    txt, ok_gtog = replace_trigger_block(txt, '{"cheats/godmode"', god_toggle)
    assert ok_gon and ok_goff and ok_gtog, f"Godmode trigger replace failed in {label}: {ok_gon},{ok_goff},{ok_gtog}"

    # Sync both cheat_options-player$ and cheat_enemyspawn$ when cycling Player slot in Settings
    txt, ok_popt = replace_trigger_block(txt, '{"cheats/options/player"', make_options_player_trigger())
    assert ok_popt, f"cheats/options/player replace failed in {label}"

    # Returning to main menu must NOT wipe cheat_enemyspawn$ back to Player 0
    whitesnoop_clean = """\t\t\t{"cheat_menu/show/0:whitesnoop"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"2.cmp_i"
\t\t\t\t\t\t\t{var "cheatmenu$"}
\t\t\t\t\t\t\t{op "=="}
\t\t\t\t\t\t\t{value 0}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t{operation hide}
\t\t\t\t\t\t{name cheat_return}
\t\t\t\t\t}
\t\t\t\t\t{"reinforcement"
\t\t\t\t\t\t{operation show}
\t\t\t\t\t\t{name cheats}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheat_menu/show/0:whitesnoop"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""
    txt, ok_ws = replace_trigger_block(txt, '{"cheat_menu/show/0:whitesnoop"', whitesnoop_clean)
    assert ok_ws, f"cheat_menu/show/0:whitesnoop replace failed in {label}"

    # Fix {functions} cheat_reinf_inf & cheat_reinf_after: freshly cloned infantry carry cheat_infantry_spawn, not cheat_enemyspawn
    for fn_hdr in ('\t\t\t{"cheat_reinf_inf"', '\t\t\t{"cheat_reinf_after"'):
        fn_start = txt.find(fn_hdr)
        assert fn_start != -1, f"Missing function {fn_hdr.strip()} in {label}"
        fn_depth = 0
        fn_end = fn_start
        for fn_i in range(fn_start, len(txt)):
            if txt[fn_i] == "{":
                fn_depth += 1
            elif txt[fn_i] == "}":
                fn_depth -= 1
                if fn_depth == 0:
                    fn_end = fn_i + 1
                    break
        fn_blk = txt[fn_start:fn_end]
        fn_blk_fixed = re.sub(
            r'(\{"player"\n\t+\{selector\n\t+\{source advanced\}\n\t+\{group\n\t+\{select\n\t+\{tag\n\t+\{tag )cheat_enemyspawn(\}\n)',
            r'\1cheat_infantry_spawn\2',
            fn_blk,
        )
        assert fn_blk_fixed.count("{tag cheat_infantry_spawn}") >= 8, f"Expected >=8 cheat_infantry_spawn in {fn_hdr.strip()}"
        txt = txt[:fn_start] + fn_blk_fixed + txt[fn_end:]

    # 9. Upgrade cheats/units/mine and cheats/units/mine_ap to spawn 8 armed mines per click
    # Fix waypoint buttons to use eventEnd (fires AFTER placing waypoint 7901 on the ground!)
    for ev_name in ("cheats/mine", "cheats/mine_ap", "cheats/ammo", "cheats/artillery", "cheats/mortar"):
        txt = txt.replace(
            f'\t\t\t\t{{eventStart "{ev_name}"}}\n\t\t\t\t{{waypoint "7901"}}',
            f'\t\t\t\t{{eventStart "cheat_click"}}\n\t\t\t\t{{eventEnd "{ev_name}"}}\n\t\t\t\t{{waypoint "7901"}}',
        )
    txt = txt.replace(
        '\t\t\t\t{eventStart "cheats/destroyarmor"}\n',
        '\t\t\t\t{eventStart "cheat_click"}\n\t\t\t\t{eventEnd "cheats/destroyarmor"}\n',
    )

    # Quote any unquoted hyphenated tags in selectors so GEM2 SDL parser never logs Unread data
    txt = txt.replace('{tag cheat_infantry-ger1}', '{tag "cheat_infantry-ger1"}')
    txt = txt.replace('{tag cheatsmod_inf-ammo}', '{tag "cheatsmod_inf-ammo"}')

    # Split combined {state "dead inactive"} in excludes into two separate {state} checks across all triggers
    txt = re.sub(
        r'(\t+)\{state\n\1\t\{state "dead inactive"\}\n\1\}',
        r'\1{state\n\1\t{state dead}\n\1}\n\1{state\n\1\t{state inactive}\n\1}',
        txt,
    )

    # Ensure bare {selector {player "X"}} in actor_state/entity_state excludes dead & inactive actors (valid nested {player} inside {include})
    txt = re.sub(
        r'(\t+)\{selector\n\1\t\{player "(\d)"\}\n\1\}',
        r'\1{selector\n\1\t{source advanced}\n\1\t{ignore_captured_by_user 0}\n\1\t{group\n\1\t\t{include\n\1\t\t\t{player\n\1\t\t\t\t{player "\2"}\n\1\t\t\t}\n\1\t\t}\n\1\t\t{exclude\n\1\t\t\t{state\n\1\t\t\t\t{state dead}\n\1\t\t\t}\n\1\t\t\t{state\n\1\t\t\t\t{state inactive}\n\1\t\t\t}\n\1\t\t}\n\1\t}\n\1}',
        txt,
    )

    # Fix any flat {player "N"} directly inside {select/{include/{exclude into valid GEM2 nested {player {player "N"}}
    txt = re.sub(
        r'(\t+)\{(select|include|exclude)\n(\1\t)\{player "(\d)"\}\n(\1)\}',
        r'\1{\2\n\3{player\n\3\t{player "\4"}\n\3}\n\5}',
        txt,
    )

    # Ensure {player} is inside {include}, never inside {select} (GEM2 {select} only accepts tag/zone/mids/inventory_items!)
    txt = re.sub(
        r'(\t+)\{select\n(\1\t\{player\n\1\t\t\{player "\d"\}\n\1\t\}\n\1\})',
        r'\1{include\n\2',
        txt,
    )

    # Remove dead outdated_game_cheat hide calls that spam game.log
    txt = txt.replace(
        '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name outdated_game_cheat}\n\t\t\t\t\t}\n',
        '',
    )

    # 9b. Rewrite cheats/units/mine, cheats/units/mine_ap, and minegetsfilled idempotently:
    #     GEM2 {"spawn"} ignores {tag}, so we select unarmed dropped mines by unique {prop cheat_mine_drop}
    #     excluding {tag mine_planted} / {tag cheat_mine_armed} / {tag hidden}, arm them for cheat_options-player$,
    #     and tag them cheat_mine_armed so they show green friendly icons and are never re-armed on later clicks.
    mine_spawns_at = "\n".join(
        '\t\t\t\t\t{"spawn"\n\t\t\t\t\t\t{entity "mine_antitank_cheat"}\n\t\t\t\t\t\t{waypoint "7901"}\n\t\t\t\t\t}'
        for _ in range(8)
    )
    new_units_mine = f"""\t\t\t{{"cheats/units/mine"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/mine"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{mine_spawns_at}
\t\t\t\t\t{{"call"
\t\t\t\t\t\t{{function "minegetsfilled"}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/mine"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/units/mine"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""
    mine_spawns_ap = "\n".join(
        '\t\t\t\t\t{"spawn"\n\t\t\t\t\t\t{entity "mine_s_cheat"}\n\t\t\t\t\t\t{waypoint "7901"}\n\t\t\t\t\t}'
        for _ in range(8)
    )
    new_units_mine_ap = f"""\t\t\t{{"cheats/units/mine_ap"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/mine_ap"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{mine_spawns_ap}
\t\t\t\t\t{{"call"
\t\t\t\t\t\t{{function "minegetsfilled"}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/mine_ap"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/units/mine_ap"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""
    txt, ok_m1 = replace_trigger_block(txt, '{"cheats/units/mine"', new_units_mine)
    txt, ok_m2 = replace_trigger_block(txt, '{"cheats/units/mine_ap"', new_units_mine_ap)
    assert ok_m1 and ok_m2, f"Mine trigger replace failed in {label}: {ok_m1}, {ok_m2}"

    mine_sel = """\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t{prop cheat_mine_drop}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag mine_planted}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag cheat_mine_armed}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag hidden}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}"""
    mine_arm_blocks = []
    for p in range(8):
        mine_arm_blocks.append(f"""\t\t\t\t{{"if"
\t\t\t\t\t{{condition
\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t}}
\t\t\t\t\t{{"mine_state"
{mine_sel}
\t\t\t\t\t\t{{action arm}}
\t\t\t\t\t\t{{miner "{p}"}}
\t\t\t\t\t}}
\t\t\t\t}}""")
    new_minegetsfilled = f"""\t\t\t{{"minegetsfilled"
\t\t\t\t{{"delay"
\t\t\t\t\t{{time 0.2}}
\t\t\t\t}}
{chr(10).join(mine_arm_blocks)}
\t\t\t\t{{"entity_state"
{mine_sel.replace(chr(9)*6, chr(9)*5)}
\t\t\t\t\t{{tag_add cheat_mine_armed}}
\t\t\t\t}}
\t\t\t}}"""
    txt, ok_mgf = replace_trigger_block(txt, '{"minegetsfilled"', new_minegetsfilled)
    assert ok_mgf, f"minegetsfilled replace failed in {label}"

    # 10. Fix Infinite Ammo: spawn ammo_cheatsmod_global, select by {prop cheatsmod_inf_ammo} (since GEM2 {"spawn"} ignores {tag})
    infammo_sel_8 = """\t\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t\t\t\t{prop cheatsmod_inf_ammo}
\t\t\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t}"""
    infammo_sel_7 = """\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t\t\t{prop cheatsmod_inf_ammo}
\t\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}"""
    infammo_player_blocks = []
    for p in range(8):
        infammo_player_blocks.append(f"""\t\t\t\t\t\t\t{{"if"
\t\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{"player"
{infammo_sel_8}
\t\t\t\t\t\t\t\t\t{{operation set}}
\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}""")
    new_infammo_trig = f"""\t\t\t{{"cheats/infammo"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheats/infammo"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"switch"
\t\t\t\t\t\t{{"case"
\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t{{var "cheat_infammo$"}}
\t\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t\t{{value 0}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_infammo$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"talk"
\t\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t\t{{tag cheat_say}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{text "mission/singlecheats/c_infammo_0"}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"spawn"
\t\t\t\t\t\t\t\t{{entity "ammo_cheatsmod_global"}}
\t\t\t\t\t\t\t\t{{waypoint "7901"}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"delay"
\t\t\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"entity_state"
{infammo_sel_7}
\t\t\t\t\t\t\t\t{{impregnability full}}
\t\t\t\t\t\t\t\t{{tag_add "cheatsmod_inf-ammo"}}
\t\t\t\t\t\t\t}}
{chr(10).join(infammo_player_blocks)}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"case"
\t\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t\t{{type cmp_i}}
\t\t\t\t\t\t\t\t{{var "cheat_infammo$"}}
\t\t\t\t\t\t\t\t{{op "=="}}
\t\t\t\t\t\t\t\t{{value 1}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t\t{{var "cheat_infammo$"}}
\t\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t\t{{value 0}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"talk"
\t\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t\t{{tag cheat_say}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{text "mission/singlecheats/c_deactivated_0"}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{"delete"
{infammo_sel_7}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/infammo"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
\t\t\t\t\t}}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/infammo"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""
    txt, _ = replace_trigger_block(txt, '{"cheats/infammo"', new_infammo_trig)

    # 11. Add {delay 1} to continuous triggers (godmodecheckon, weakenemy, fuel_on) so they don't run 60x/sec
    #     AND strip any legacy blanket {state user_control} blocks so AI bots in Conquest/Skirmish are NEVER buffed!
    god_uc = '\t\t\t\t\t{"entity_state"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{impregnability full}\n\t\t\t\t\t}\n'
    fuel_uc = '\t\t\t\t\t{"actor_state"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t{exclude\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state dead}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state inactive}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{human\n\t\t\t\t\t\t\t{stamina 100}\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t\t{"inventory"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t{exclude\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state dead}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state inactive}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{action fuel}\n\t\t\t\t\t\t{amount 999}\n\t\t\t\t\t}\n'
    txt = txt.replace(god_uc, "")
    txt = txt.replace(fuel_uc, "")
    for trig, sec in [
        ('{"cheats/active/godmodecheckon"', "1"),
        ('{"cheats/active/weakenemy"', "1"),
        ('{"cheats/active/fuel_on"', "1.5"),
    ]:
        pat = re.escape(trig) + r'(\n\t\t\t\t\{condition.*?\{actions\n)'
        m = re.search(pat, txt, re.S)
        if m and '{"delay"' not in txt[m.end() : m.end() + 60]:
            txt = txt[: m.end()] + f'\t\t\t\t\t{{"delay"\n\t\t\t\t\t\t{{time {sec}}}\n\t\t\t\t\t}}\n' + txt[m.end() :]

    # Verify zero flat {player "..."} inside {select/{include/{exclude (breaks GEM2 advanced group filtering!)
    flat_players = re.findall(r'\{(?:select|include|exclude)\n\t+\{player "[^"]+"\}', txt)
    assert not flat_players, f"Flat {{player}} inside advanced group found in {label}: {len(flat_players)}"

    # Strict GEM2 {select} whitelist check: only inventory_items, mids, tag, zone, zone_ex are valid in {select}
    valid_select = {"inventory_items", "mids", "tag", "zone", "zone_ex"}
    illegal_select = {}
    lines_chk = txt.splitlines()
    for i_chk, l_chk in enumerate(lines_chk):
        if l_chk.strip() == "{select":
            ind = l_chk[: len(l_chk) - len(l_chk.lstrip("\t"))]
            c_ind = ind + "\t"
            for j_chk in range(i_chk + 1, len(lines_chk)):
                if lines_chk[j_chk] == ind + "}":
                    break
                if lines_chk[j_chk].startswith(c_ind + "{") and not lines_chk[j_chk].startswith(c_ind + "\t"):
                    kw = lines_chk[j_chk].strip().split()[0].lstrip("{").rstrip("}")
                    if kw not in valid_select:
                        illegal_select[kw] = illegal_select.get(kw, 0) + 1
    assert not illegal_select, f"Illegal {{select}} children in {label}: {illegal_select}"

    # Verify zero Chinese characters remain
    cn_left = re.findall(r"[\u4e00-\u9fff]+", txt)
    assert not cn_left, f"Chinese still found in {label}: {cn_left[:10]}"

    # Verify balanced braces
    opens = txt.count("{")
    closes = txt.count("}")
    assert opens == closes, f"Brace mismatch in {label}: {{={opens}, }}={closes}"

    # Verify strict variable scoping so non-Conquest maps never crash on undeclared Conquest variables
    m_vars = re.search(r"\{vars\s*(.*?)\n\t\}", txt, re.S)
    assert m_vars, f"Missing {{vars}} block in {label}"
    declared_vars = set(re.findall(r'\{"([^"]+)"', m_vars.group(1)))
    used_vars = set(re.findall(r'\{var "([^"]+?)\$"', txt))
    undeclared = used_vars - declared_vars
    allowed_dcg = (
        {"id_1st_player", "enemyid", "id_1st_enemy", "id_defenderbot", "gameover_request_player_win"}
        if is_dcg
        else set()
    )
    assert undeclared <= allowed_dcg, f"Unexpected undeclared vars in {label} (is_dcg={is_dcg}): {sorted(undeclared - allowed_dcg)}"

    # Verify all waypoints sit strictly inside GEM2's 8192-entry waypoint bitmap (0..8191)
    assert not re.search(r'"3000\d"', txt), f"Out-of-bounds 3000x waypoint still present in {label}"
    wp_pos = txt.find("{waypoints")
    assert wp_pos != -1, f"Missing {{waypoints block in {label}"
    wp_depth, wp_end = 0, wp_pos
    for k in range(wp_pos, len(txt)):
        if txt[k] == "{":
            wp_depth += 1
        elif txt[k] == "}":
            wp_depth -= 1
            if wp_depth == 0:
                wp_end = k + 1
                break
    declared_wps = [int(w) for w in re.findall(r'\{"(\d+)"', txt[wp_pos:wp_end])]
    assert declared_wps and all(0 <= w < 8192 for w in declared_wps), f"Out-of-bounds waypoint in {label}: {declared_wps}"

    print(f"Patched {label}: addexp={ok1}, destroyarmor={ok2}, aimrange={ok3}, braces OK ({opens}), vars OK (undeclared={sorted(undeclared)}), wps={declared_wps}, zero Chinese.")
    return txt.replace("\n", "\r\n")


def rewrite_cheatsmod_pak():
    ext_mod = """{Modifiers
\t{modifier
\t\t{name cheat_armor}
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_armor}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{armor
\t\t\t\t{scale 0.01}
\t\t\t}
\t\t}
\t}
\t{modifier
\t\t{name cheat_armor_disabled}
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_armor_disabled}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{armor
\t\t\t\t{scale 1}
\t\t\t}
\t\t}
\t}
\t{modifier
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{aim_range
\t\t\t\t{place "*"}
\t\t\t\t{scale 999}
\t\t\t}
\t\t}
\t}
\t{modifier
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{accuracy
\t\t\t\t{place "*"}
\t\t\t\t{scale 999}
\t\t\t}
\t\t}
\t}
}
"""
    opt_tags = """\t{"cheats_option_select" "<s(25)><c(204 204 204)> \\nCheatsMod: <c(20a601)>2.6 Reworked<c(204 204 204)>"}
\t{"cheats_country_select" "Set Faction:"}
\t{"nada" ""}
\t{"germany" "Axis"}
\t{"usa" "Allies"}
\t{"russian" "USSR"}
\t{"common_wealth" "Commonwealth"}
\t{"japan" "Japan"}
"""
    cm_pak = os.path.join(MOD, "resource", "map", "cheatsmod.pak")
    tmp_cm = cm_pak + ".tmp"
    with zipfile.ZipFile(cm_pak, "r") as zin, zipfile.ZipFile(tmp_cm, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            nl = item.filename.lower()
            if nl == "cheatsmod/cheats_dcg.mi":
                continue
            elif nl == "cheatsmod/extension.mod":
                zout.writestr(item.filename, ext_mod.replace("\n", "\r\n").encode("utf-8"))
            elif nl == "cheatsmod/option_tags.mi":
                zout.writestr(item.filename, opt_tags.replace("\n", "\r\n").encode("utf-8"))
            elif nl == "cheatsmod/cheats.mi":
                raw = zin.read(item.filename).decode("utf-8", errors="replace")
                patched = patch_mi_content(raw, "cheatsmod/cheats.mi", is_dcg=False)
                zout.writestr("cheatsmod/cheats.mi", patched.encode("utf-8"))
                patched_dcg = patch_mi_content(raw, "cheatsmod/cheats_dcg.mi", is_dcg=True)
                zout.writestr("cheatsmod/cheats_dcg.mi", patched_dcg.encode("utf-8"))
            elif nl == "cheatsmod/m_cheats.mi":
                raw = zin.read(item.filename).decode("utf-8", errors="replace")
                patched = patch_mi_content(raw, "cheatsmod/m_cheats.mi", is_dcg=False)
                zout.writestr(item.filename, patched.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp_cm, cm_pak)
    print("Rebuilt cheatsmod.pak successfully.")


def rewrite_modtanks_entity_mi():
    mt_dir = os.path.join(MOD, "resource", "modtanks_configuration")
    ent_mi_path = os.path.join(mt_dir, "entity.mi")
    content = (
        '\t{Entity "sdkfz7" 0xfe01        {Position 10 1}        {Player 0}        {MID 9801}    }    {Tags "csp_1" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe01}\r\n'
        '\t{Entity "pz35t" 0xfe02        {Position 20 1}        {Player 0}        {MID 9802}    }    {Tags "csp_2" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe02}\r\n'
        '\t{Entity "stug3g" 0xfe03        {Position 30 1}        {Player 0}        {MID 9803}    }    {Tags "csp_3" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe03}\r\n'
        '\t{Entity "tiger1hunt" 0xfe04        {Position 40 1}        {Player 0}        {MID 9804}    }    {Tags "csp_4" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe04}\r\n'
        '\t{Human "mp/ger/mid/flamer" 0xfe05        {Position 10 100}        {Player 0}        {MID 9805}    }    {Tags "hsp_1" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe05}\r\n'
        '\t{Human "mp/rus/mid/rifle" 0xfe06        {Position 20 100}        {Player 0}        {MID 9806}    }    {Tags "hsp_2" "cheat_delete" "hidden" "cheat_infantry_spawn" 0xfe06}\r\n'
    )
    os.makedirs(mt_dir, exist_ok=True)
    with open(ent_mi_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    for mi_name in ("rfm.mi", "spawn.mi"):
        p = os.path.join(mt_dir, mi_name)
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
        txt = txt.replace('"30000"', '"7900"').replace('"30001"', '"7901"')
        assert not re.search(r"3000\d", txt), f"Out-of-bounds 3000x waypoint still present in {mi_name}"
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(txt.replace("\r\n", "\n").replace("\n", "\r\n"))
    print("Rewrote modtanks_configuration/{entity,rfm,spawn}.mi with unique IDs (0xfe01..0xfe06) & safe waypoints (7900..7901).")


def rebuild_map_paks():
    """Rebuild single.pak (91 maps) and multi.pak (388 maps) cleanly from pure vanilla v1.069.0 + DLC paks."""
    res_dir = os.path.join(GOH_DIR, "resource")
    single_maps = {}
    multi_maps = {}

    def collect(pak_path, strip_prefix=""):
        with zipfile.ZipFile(pak_path, "r") as z:
            for item in z.infolist():
                nl = item.filename.lower()
                if not nl.endswith(".mi"):
                    continue
                rel = item.filename[len(strip_prefix) :] if strip_prefix and nl.startswith(strip_prefix) else item.filename
                rel_l = rel.lower()
                if rel_l.startswith("single/"):
                    single_maps[rel] = (item, z.read(item.filename))
                elif rel_l.startswith("multi/"):
                    multi_maps[rel] = (item, z.read(item.filename))

    collect(os.path.join(res_dir, "map", "single.pak"))
    collect(os.path.join(res_dir, "map", "multi.pak"))
    for dlc_pak in sorted(glob.glob(os.path.join(res_dir, "*dlc*.pak"))):
        collect(dlc_pak, "map/")

    def patch_and_write(out_pak, entries_dict, expected_total, expected_dcg):
        tmp_pak = out_pak + ".tmp"
        dcg_count = 0
        non_dcg_count = 0
        with zipfile.ZipFile(tmp_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for rel in sorted(entries_dict):
                orig_item, raw = entries_dict[rel]
                txt = raw.decode("utf-8", errors="replace").lstrip("\ufeff").replace("\r\n", "\n")
                lines = txt.split("\n")
                assert lines[0].lstrip().startswith("{mission"), f"Map {rel} does not start with {{mission"
                is_dcg = "dcg_vars.inc" in txt
                if is_dcg:
                    dcg_count += 1
                    inc_line = '(include "/map/cheatsmod/cheats_dcg.mi")'
                else:
                    non_dcg_count += 1
                    inc_line = '(include "/map/cheatsmod/cheats.mi")'
                assert "type_3a_mine" not in txt, f"Found MACE-only type_3a_mine in vanilla map {rel}!"
                lines.insert(1, inc_line)
                out_bytes = ("\r\n".join(lines)).encode("utf-8")
                dt = orig_item.date_time if orig_item.date_time[0] >= 1980 else (2020, 1, 1, 0, 0, 0)
                zi = zipfile.ZipInfo(rel, date_time=dt)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(zi, out_bytes)
        os.replace(tmp_pak, out_pak)
        assert dcg_count + non_dcg_count == expected_total, f"Expected {expected_total} maps in {out_pak}, got {dcg_count + non_dcg_count}"
        assert dcg_count == expected_dcg, f"Expected {expected_dcg} DCG maps in {out_pak}, got {dcg_count}"
        print(f"Rebuilt {os.path.basename(out_pak)}: {expected_total} maps ({dcg_count} DCG -> cheats_dcg.mi, {non_dcg_count} non-DCG -> cheats.mi).")

    map_dir = os.path.join(MOD, "resource", "map")
    patch_and_write(os.path.join(map_dir, "single.pak"), single_maps, 91, 0)
    patch_and_write(os.path.join(map_dir, "multi.pak"), multi_maps, 388, 114)


if __name__ == "__main__":
    remove_chinese_docs()
    rewrite_localization()
    write_conquest_budget_files()
    rewrite_supply_and_entities()
    generate_custom_button_icons()
    rewrite_modtanks_entity_mi()
    rewrite_cheatsmod_pak()
    rebuild_map_paks()
    print("ALL REWORK STEPS COMPLETED!")
