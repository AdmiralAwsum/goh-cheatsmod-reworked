import io
import os
import re
import zipfile
from PIL import Image, ImageDraw

MOD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mod")


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
        "c_weakenemy_0": "Enabled: Instakill Enemies (Infantry & Vehicles)",
        "cheatversion": "<s(25)><c(204 204 204)>CheatsMod <c(40c040)>2.6 Reworked<c(204 204 204)><s(8)>",
        "cheatversion1": "<c(40c040)>v2.6 Reworked",
        "c_deactivated_0": "Cheat Deactivated",
        "cheats_option_select": "Cheat Settings:",
        "Autoassign": "<e(shadow)><c(f2c200)>Auto-Assign</c></e>",
        "Set to player0": "Override Player 0 (All cheats already auto-target human units; click to cycle)",
        "Set to player1": "Override Player 1 (All cheats already auto-target human units; click to cycle)",
        "Set to player2": "Override Player 2 (All cheats already auto-target human units; click to cycle)",
        "Set to player3": "Override Player 3 (All cheats already auto-target human units; click to cycle)",
        "Set to player4": "Override Player 4 (All cheats already auto-target human units; click to cycle)",
        "Set to player5": "Override Player 5 (All cheats already auto-target human units; click to cycle)",
        "Set to player6": "Override Player 6 (All cheats already auto-target human units; click to cycle)",
        "Set to player7": "Override Player 7 (All cheats already auto-target human units; click to cycle)",
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

    # Insert Fast Miner + missing player4..7 tags before final '}'
    extra_tags = [
        '\t{"Fast Miner" "Fast Mine Engineer"}',
        '\t{"Fast Miner hint" "Click on ground to spawn Engineer with 40 AT + 40 AP instant (0.1s) mines. Hold Shift to queue!"}',
        '\t{"Set to player4" "Override Player 4 (All cheats already auto-target human units; click to cycle)"}',
        '\t{"Set to player5" "Override Player 5 (All cheats already auto-target human units; click to cycle)"}',
        '\t{"Set to player6" "Override Player 6 (All cheats already auto-target human units; click to cycle)"}',
        '\t{"Set to player7" "Override Player 7 (All cheats already auto-target human units; click to cycle)"}',
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
\t{props "antitank"}
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
\t{props "bounding" "antipersonnel"}
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
\t{props "vision_lev00_can" "ammo_crate" "no_recrew_logic"}
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
    with zipfile.ZipFile(ent_pak, "r") as zin, zipfile.ZipFile(tmp_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            nl = item.filename.lower()
            if nl == "inventory/mine_antitank/mine_antitank_cheat.def":
                zout.writestr(item.filename, mine_at_def.encode("utf-8"))
            elif nl == "inventory/mine_ap/mine_s_cheat.def":
                zout.writestr(item.filename, mine_ap_def.encode("utf-8"))
            elif nl == "service/ammo_cheatsmod_global/ammo_cheatsmod_global.def":
                continue
            else:
                zout.writestr(item, zin.read(item.filename))
        zout.writestr("service/ammo_cheatsmod_global/ammo_cheatsmod_global.def", ammo_global_def.encode("utf-8"))
    os.replace(tmp_pak, ent_pak)
    print("Updated entity.pak (instant-plant mines + ammo_cheatsmod_global).")

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
    blocks = []
    # Always apply to all human-controlled units (Solo & Co-op) via {state user_control}
    blocks.append("""\t\t\t\t\t{"actor_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{select
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state user_control}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{include
\t\t\t\t\t\t\t\t\t{prop
\t\t\t\t\t\t\t\t\t\t{prop human}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state "dead inactive"}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\t{human
\t\t\t\t\t\t\t{veterancy 8}
\t\t\t\t\t\t}
\t\t\t\t\t}""")
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
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{prop
\t\t\t\t\t\t\t\t\t\t\t{{prop human}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
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


def make_auto_detect_player_trigger():
    """Auto-detects the actual human player slot (0-7) using {select {player}} AND {state user_control}."""
    user_checks = []
    # Check 7..2, then 0, then 1 so Player 1 (Conquest/MP) or Player 0 (SP) wins cleanly
    for p in [7, 6, 5, 4, 3, 2, 0, 1]:
        user_checks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type entities}}
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state user_control}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{"set_i"
\t\t\t\t\t\t\t{{var "cheat_options-player$"}}
\t\t\t\t\t\t\t{{op "="}}
\t\t\t\t\t\t\t{{value {p}}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}""")
    return f"""\t\t\t{{"cheats/auto_detect_player"
\t\t\t\t{{condition
\t\t\t\t}}
\t\t\t\t{{actions
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 2}}
\t\t\t\t\t}}
{chr(10).join(user_checks)}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 4}}
\t\t\t\t\t}}
{chr(10).join(user_checks)}
\t\t\t\t}}
\t\t\t}}"""


def make_repair_trigger():
    comps = ["body", "turret", "gun", "engine", "trackleft", "trackright", "wheel", "shield", "mantlet", "cabin"]
    blocks = []
    # Always repair all human-controlled vehicles (Solo & Co-op) via {state user_control}
    uc_cmds = []
    for c in comps:
        uc_cmds.append(f"""\t\t\t\t\t{{"actor_component"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t{{state user_control}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t{{prop
\t\t\t\t\t\t\t\t\t\t{{prop vehicle}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{component {c}}}
\t\t\t\t\t\t{{state work}}
\t\t\t\t\t}}""")
    blocks.append(chr(10).join(uc_cmds))
    for p in range(8):
        comp_cmds = []
        for c in comps:
            comp_cmds.append(f"""\t\t\t\t\t\t{{"actor_component"
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag _user}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{prop
\t\t\t\t\t\t\t\t\t\t\t{{prop vehicle}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t{{component {c}}}
\t\t\t\t\t\t\t{{state work}}
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
    return f"""\t\t\t{{"cheats/active/repair"
\t\t\t\t{{condition
\t\t\t\t\t{{terms
\t\t\t\t\t\t{{"1.event"
\t\t\t\t\t\t\t{{id "cheat_repair"}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\t{{actions
{chr(10).join(blocks)}
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
    blocks = ["""\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t{source advanced}
\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t{group
\t\t\t\t\t\t\t\t{select
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state user_control}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{exclude
\t\t\t\t\t\t\t\t\t{tag
\t\t\t\t\t\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t{state
\t\t\t\t\t\t\t\t\t\t{state "dead inactive"}
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\t{tag_add cheat_aimrange}
\t\t\t\t\t}"""]
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
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag _user}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t{{exclude
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_aimrange}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{state
\t\t\t\t\t\t\t\t\t\t\t{{state "dead inactive"}}
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
\t\t\t\t\t\t{{time 1.5}}
\t\t\t\t\t}}
{chr(10).join(blocks)}
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/aimrange"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


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
\t\t\t\t\t\t{{waypoint "30001"}}
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


def make_conquest_win_trigger():
    return """\t\t\t{"cheats/active/conquest_win"
\t\t\t\t{condition
\t\t\t\t\t{terms
\t\t\t\t\t\t{"1.event"
\t\t\t\t\t\t\t{id "cheats/conquest_win"}
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\t{actions
\t\t\t\t\t{"set_i"
\t\t\t\t\t\t{var "gameover_request_player_win$"}
\t\t\t\t\t\t{op "="}
\t\t\t\t\t\t{value 1}
\t\t\t\t\t}
\t\t\t\t\t{"sound"
\t\t\t\t\t\t{name "mission/task_fulfilled"}
\t\t\t\t\t}
\t\t\t\t\t{"event"
\t\t\t\t\t\t{event "cheats/conquest_win"}
\t\t\t\t\t\t{mode reset}
\t\t\t\t\t\t{delay 0}
\t\t\t\t\t}
\t\t\t\t\t{"delay"
\t\t\t\t\t\t{time 0.1}
\t\t\t\t\t}
\t\t\t\t\t{"trigger"
\t\t\t\t\t\t{name "cheats/active/conquest_win"}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}"""


def write_conquest_budget_files():
    """Copy Increased call-in stages resources_*.set and boost Budget to 2000 CP + 2.0/s so all waves deploy immediately."""
    ws_inc = r"D:\SteamLibrary\steamapps\workshop\content\400750\3370969203\resource\set\dynamic_campaign"
    out_dc = os.path.join(MOD, "resource", "set", "dynamic_campaign")
    os.makedirs(out_dc, exist_ok=True)
    for fname in ("resources_low.set", "resources_standard.set", "resources_high.set", "resources_very_high.set"):
        with open(os.path.join(ws_inc, fname), "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
        txt = re.sub(
            r'\{Start\s+"[^"]+"\}',
            '{Start "0:2000 4:2000 8:2000 12:2000 16:2000 20:2000"}',
            txt,
        )
        txt = re.sub(r'\{PointsPerSecond\s+[0-9.]+\}', '{PointsPerSecond 2.0}', txt)
        txt = re.sub(r'\{Limit\s+\d+\}', '{Limit 2000}', txt)
        with open(os.path.join(out_dc, fname), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(txt)
    print("Wrote 2000-CP Conquest Budget resources_*.set files.")


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
    new_lines = lines[:start_idx] + new_block.splitlines() + lines[end_idx + 1 :]
    return "\n".join(new_lines), True


def generate_custom_button_icons():
    """Generate crisp 104x52 3-state (_00, _01, _02) TGA icons in interface.pak using menu_item as the base plate."""
    iface_pak = os.path.join(MOD, "resource", "interface.pak")
    tmp_pak = iface_pak + ".tmp"

    def draw_star(draw, cx, cy, r_outer, r_inner, fill, outline):
        import math
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            r = r_outer if i % 2 == 0 else r_inner
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=fill, outline=outline)

    def draw_repair(draw):
        # Gold wrench on right side (x ~ 76, y ~ 26)
        draw.line([(66, 36), (86, 16)], fill=(235, 195, 70, 255), width=5)
        draw.ellipse([80, 10, 94, 24], fill=(235, 195, 70, 255), outline=(40, 30, 10, 255))
        draw.polygon([(86, 16), (95, 11), (92, 20)], fill=(45, 45, 45, 255))
        draw.ellipse([60, 31, 71, 42], fill=(235, 195, 70, 255), outline=(40, 30, 10, 255))

    def draw_destroyarmor(draw):
        # Red target crosshair + X
        draw.ellipse([66, 12, 92, 38], outline=(235, 70, 60, 255), width=3)
        draw.line([(79, 8), (79, 42)], fill=(235, 70, 60, 255), width=2)
        draw.line([(62, 25), (96, 25)], fill=(235, 70, 60, 255), width=2)
        draw.ellipse([75, 21, 83, 29], fill=(255, 190, 60, 255))

    def draw_veterancy(draw):
        # Bright gold star + double chevron
        draw_star(draw, 79, 20, 11, 4.5, (255, 215, 65, 255), (60, 40, 10, 255))
        draw.line([(69, 35), (79, 30), (89, 35)], fill=(255, 215, 65, 255), width=3)
        draw.line([(69, 41), (79, 36), (89, 41)], fill=(255, 215, 65, 255), width=3)

    def draw_win(draw):
        # Emerald badge + gold victory star
        draw.ellipse([65, 12, 93, 40], fill=(35, 140, 75, 240), outline=(240, 200, 75, 255), width=2)
        draw_star(draw, 79, 26, 10, 4.2, (255, 220, 75, 255), (40, 30, 10, 255))

    def draw_fastminer(draw):
        # Mine disc + yellow speed bolt
        draw.ellipse([65, 22, 87, 38], fill=(160, 170, 155, 255), outline=(30, 35, 30, 255), width=2)
        draw.rectangle([72, 18, 80, 23], fill=(210, 180, 70, 255))
        draw.polygon([(88, 10), (80, 25), (86, 25), (82, 40), (94, 22), (87, 22)], fill=(255, 220, 50, 255), outline=(40, 30, 10, 255))

    def draw_menu_spawn(draw):
        # Clean tank/unit silhouette arrow on right
        draw.rectangle([65, 24, 90, 34], fill=(185, 200, 175, 255), outline=(30, 35, 30, 255))
        draw.rectangle([71, 18, 84, 24], fill=(185, 200, 175, 255), outline=(30, 35, 30, 255))
        draw.line([(84, 21), (95, 21)], fill=(220, 225, 210, 255), width=3)

    def draw_menu_cheats(draw):
        # Clean gold shield/star emblem
        draw_star(draw, 79, 26, 12, 5, (255, 205, 60, 255), (50, 35, 10, 255))

    def draw_menu_settings(draw):
        # Clean gear ring
        draw.ellipse([68, 15, 90, 37], outline=(190, 205, 220, 255), width=4)
        draw.ellipse([75, 22, 83, 30], fill=(50, 52, 48, 255))

    def draw_menu_support(draw):
        # Clean supply/support cross + chevron
        draw.rectangle([76, 14, 82, 38], fill=(215, 190, 85, 255))
        draw.rectangle([67, 23, 91, 29], fill=(215, 190, 85, 255))

    icon_drawers = {
        "repair": draw_repair,
        "destroyarmor": draw_destroyarmor,
        "veterancy": draw_veterancy,
        "win": draw_win,
        "fastminer": draw_fastminer,
        "menu_spawn": draw_menu_spawn,
        "menu_cheats": draw_menu_cheats,
        "menu_settings": draw_menu_settings,
        "menu_support": draw_menu_support,
    }

    with zipfile.ZipFile(iface_pak, "r") as zin, zipfile.ZipFile(tmp_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        base_plates = {}
        for state in ("00", "01", "02"):
            raw = zin.read(f"interface/scene/unit_icon/whitesnoop/cheats/disabled_{state}.tga")
            plate = Image.open(io.BytesIO(raw)).convert("RGBA")
            # Crop/fill out the top red status strip (y=0..8) with clean dark metallic border so it looks like a neutral action button
            d_clean = ImageDraw.Draw(plate)
            d_clean.rectangle([4, 2, 99, 8], fill=(55, 58, 52, 255))
            base_plates[state] = plate

        generated_names = set()
        for icon_name, drawer in icon_drawers.items():
            for state in ("00", "01", "02"):
                out_name = f"interface/scene/unit_icon/whitesnoop/cheats/{icon_name}_{state}.tga"
                generated_names.add(out_name.lower())

        for item in zin.infolist():
            if item.filename.lower() in generated_names:
                continue
            zout.writestr(item, zin.read(item.filename))

        for icon_name, drawer in icon_drawers.items():
            for state in ("00", "01", "02"):
                im = base_plates[state].copy()
                d = ImageDraw.Draw(im)
                drawer(d)
                buf = io.BytesIO()
                im.save(buf, format="TGA")
                out_name = f"interface/scene/unit_icon/whitesnoop/cheats/{icon_name}_{state}.tga"
                zout.writestr(out_name, buf.getvalue())

    os.replace(tmp_pak, iface_pak)
    print("Generated 5 custom 3-state TGA button icons in interface.pak.")


def patch_mi_content(raw_txt, label):
    txt = raw_txt.replace("\r\n", "\n")

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

    # 2. Register new events "cheats/fast_miner" and "cheats/conquest_win"
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
\t\t\t\t{waypoint "30001"}
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
        "cheat_addmoney": ('"+1000 MP"', None, '"Add +1000 Manpower / Reinforcement Points (Skirmish & Singleplayer)"'),
        "cheat_godmode_off": ('"God Mode"', None, '"Enable: make all your units and vehicles invulnerable"'),
        "cheat_godmode_on": ('"God Mode"', None, '"Disable: turn off God Mode"'),
        "cheat_infammo_off": ('"Infinite Ammo"', None, '"Enable: spawn a map-wide (500m) resupply aura refilling ammo & fuel"'),
        "cheat_infammo_on": ('"Infinite Ammo"', None, '"Disable: remove map-wide resupply aura"'),
        "cheat_fuel-stam-off": ('"Fuel & Stamina"', None, '"Enable: keep soldier stamina at 100% and vehicle fuel full"'),
        "cheat_fuel-stam-on": ('"Fuel & Stamina"', None, '"Disable: turn off infinite fuel & stamina"'),
        "cheat_aimrange_accuracy_on": ('"Range & Accuracy"', None, '"Enable: grant 3x weapon range and 5x accuracy to your units"'),
        "cheat_aimrange_accuracy_off": ('"Range & Accuracy"', None, '"Disable: restore normal weapon range and accuracy"'),
        "cheat_enemy": ('"Enemy Cheats"', None, '"Cheats below target enemy units on the map"'),
        "cheatweakenemy": ('"Instakill"', None, '"Enable: reduce enemy soldier HP to 1 and enemy vehicle armor to 1%"'),
        "cheatweakenemyoff": ('"Instakill"', None, '"Disable: restore normal enemy HP and armor"'),
        "cheat_addexp": ('"Max Veterancy"', '"whitesnoop/cheats/veterancy"', '"One-shot: promote all currently alive friendly infantry, gun crews, and vehicle crews to Level 8"'),
        "cheat_conquest_win": ('"Instant Win"', '"whitesnoop/cheats/win"', '"Immediately win the current Conquest battle with full victory rewards"'),
        "cheat_repair": ('"Repair Vehicles"', '"whitesnoop/cheats/repair"', '"Instantly repair hull, turret, gun, engine, tracks & wheels on all your vehicles"'),
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
        "changecn_user": ('"Side: Ally"', None, '"Spawning units for your own team (click to switch to Enemy AI)"'),
        "changecn_ai": ('"Side: Enemy AI"', None, '"Spawning units for Enemy AI (click to switch to Ally)"'),
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
    for btn_id, (new_text, new_img, new_hint) in button_updates.items():
        bpat = re.compile(
            r'(\t\t\t\{"' + re.escape(btn_id) + r'"\n\t\t\t\t\{state hidden\}\n)\t\t\t\t\{text [^\n]+\}\n(\t\t\t\t\{image [^\n]+\}\n)\t\t\t\t\{hint [^\n]+\}\n'
        )
        m = bpat.search(txt)
        if m:
            img_line = f'\t\t\t\t{{image {new_img}}}\n' if new_img else m.group(2)
            rep = f'{m.group(1)}\t\t\t\t{{text {new_text}}}\n{img_line}\t\t\t\t{{hint {new_hint}}}\n'
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

    # Fix swapped aimrange icons: when cheat_aimrange$ != 1 show _off (red), when == 1 show _on (green)
    old_aim_show = """\t\t\t\t\t{"if"
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
    new_aim_show = old_aim_show.replace("cheat_aimrange_accuracy_on", "__TMP__").replace("cheat_aimrange_accuracy_off", "cheat_aimrange_accuracy_on").replace("__TMP__", "cheat_aimrange_accuracy_off")
    if old_aim_show in txt:
        txt = txt.replace(old_aim_show, new_aim_show, 1)

    # 7. Initialize cheat_options-player$ = 0 and explicitly reset one-shot events in cheats/set/vars
    if '{var "cheat_options-player$"}' not in txt[:16000]:
        txt = txt.replace(
            '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_infammo$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_infammo$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_options-player$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/addexp"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/conquest_win"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheat_repair"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/destroyarmor"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"event"\n\t\t\t\t\t\t{event "cheats/fast_miner"}\n\t\t\t\t\t\t{mode reset}\n\t\t\t\t\t\t{delay 0}\n\t\t\t\t\t}',
            1,
        )

    # 8. Replace broken triggers with fixed ones + add auto_detect_player + conquest_win
    txt, ok1 = replace_trigger_block(
        txt,
        '{"cheats/active/addexp"',
        make_auto_detect_player_trigger() + "\n" + make_addexp_trigger() + "\n" + make_repair_trigger() + "\n" + make_conquest_win_trigger() + "\n" + make_miner_trigger(),
    )
    txt, ok2 = replace_trigger_block(txt, '{## "cheats/destroyarmor"', make_destroyarmor_trigger())
    txt, ok3 = replace_trigger_block(txt, '{"cheats/active/aimrange"', make_aimrange_trigger())

    # 9. Upgrade cheats/units/mine and cheats/units/mine_ap to spawn 8 armed mines per click
    # Fix waypoint buttons to use eventEnd (fires AFTER placing waypoint 30001 on the ground!)
    for ev_name in ("cheats/mine", "cheats/mine_ap", "cheats/ammo", "cheats/artillery", "cheats/mortar"):
        txt = txt.replace(
            f'\t\t\t\t{{eventStart "{ev_name}"}}\n\t\t\t\t{{waypoint "30001"}}',
            f'\t\t\t\t{{eventStart "cheat_click"}}\n\t\t\t\t{{eventEnd "{ev_name}"}}\n\t\t\t\t{{waypoint "30001"}}',
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

    # Ensure bare {selector {player "X"}} in actor_state/entity_state excludes dead & inactive actors
    txt = re.sub(
        r'(\t+)\{selector\n\1\t\{player "(\d)"\}\n\1\}',
        r'\1{selector\n\1\t{source advanced}\n\1\t{ignore_captured_by_user 0}\n\1\t{group\n\1\t\t{select\n\1\t\t\t{player "\2"}\n\1\t\t}\n\1\t\t{exclude\n\1\t\t\t{state\n\1\t\t\t\t{state dead}\n\1\t\t\t}\n\1\t\t\t{state\n\1\t\t\t\t{state inactive}\n\1\t\t\t}\n\1\t\t}\n\1\t}\n\1}',
        txt,
    )

    # Remove dead outdated_game_cheat hide calls that spam game.log
    txt = txt.replace(
        '\t\t\t\t\t{"reinforcement"\n\t\t\t\t\t\t{operation hide}\n\t\t\t\t\t\t{name outdated_game_cheat}\n\t\t\t\t\t}\n',
        '',
    )

    old_mine_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_antitank_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t}"""
    new_mine_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_antitank_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t\t{tag cheat_mine}
\t\t\t\t\t}"""
    if txt.count(old_mine_spawn) == 4:
        txt = txt.replace(old_mine_spawn, new_mine_spawn + "\n" + new_mine_spawn)

    old_mine_ap_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_s_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t}"""
    new_mine_ap_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_s_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t\t{tag cheat_mine}
\t\t\t\t\t}"""
    if txt.count(old_mine_ap_spawn) == 4:
        txt = txt.replace(old_mine_ap_spawn, new_mine_ap_spawn + "\n" + new_mine_ap_spawn)

    # Faster arming in minegetsfilled (0.2s) and use cheat_options-player$ when cheat_enemyspawn$ == 0
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
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_mine}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
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
\t\t\t\t\t{{selector
\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t{{tag cheat_mine}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\t{{tag_remove cheat_mine}}
\t\t\t\t}}
\t\t\t}}"""
    txt, _ = replace_trigger_block(txt, '{"minegetsfilled"', new_minegetsfilled)

    # 10. Fix Infinite Ammo: spawn ammo_cheatsmod_global when turned ON, delete when turned OFF
    old_infammo_on = """\t\t\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag "cheatsmod_inf-ammo"}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{tag_remove hidden}
\t\t\t\t\t\t\t\t{inactive off}
\t\t\t\t\t\t\t}"""
    new_infammo_on = """\t\t\t\t\t\t\t{"spawn"
\t\t\t\t\t\t\t\t{entity "ammo_cheatsmod_global"}
\t\t\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t\t\t\t{tag cheatsmod_inf-ammo}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag "cheatsmod_inf-ammo"}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{impregnability full}
\t\t\t\t\t\t\t\t{tag_remove hidden}
\t\t\t\t\t\t\t\t{inactive off}
\t\t\t\t\t\t\t}"""
    if old_infammo_on in txt:
        txt = txt.replace(old_infammo_on, new_infammo_on, 1)

    old_infammo_off = """\t\t\t\t\t\t\t{"entity_state"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag "cheatsmod_inf-ammo"}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t{tag_add hidden}
\t\t\t\t\t\t\t\t{inactive on}
\t\t\t\t\t\t\t}"""
    new_infammo_off = """\t\t\t\t\t\t\t{"delete"
\t\t\t\t\t\t\t\t{selector
\t\t\t\t\t\t\t\t\t{ignore_captured_by_user 0}
\t\t\t\t\t\t\t\t\t{tag "cheatsmod_inf-ammo"}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}"""
    if old_infammo_off in txt:
        txt = txt.replace(old_infammo_off, new_infammo_off, 1)

    # 11. Add {delay 1} to continuous triggers (godmodecheckon, weakenemy, fuel_on) so they don't run 60x/sec
    #     AND prepend {state user_control} blocks to godmodecheckon & fuel_on so they always work automatically!
    god_uc = '\t\t\t\t\t{"entity_state"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{impregnability full}\n\t\t\t\t\t}\n'
    fuel_uc = '\t\t\t\t\t{"actor_state"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t{exclude\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state dead}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state inactive}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{human\n\t\t\t\t\t\t\t{stamina 100}\n\t\t\t\t\t\t}\n\t\t\t\t\t}\n\t\t\t\t\t{"inventory"\n\t\t\t\t\t\t{selector\n\t\t\t\t\t\t\t{source advanced}\n\t\t\t\t\t\t\t{ignore_captured_by_user 0}\n\t\t\t\t\t\t\t{group\n\t\t\t\t\t\t\t\t{select\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state user_control}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t{exclude\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state dead}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t{state\n\t\t\t\t\t\t\t\t\t\t{state inactive}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t}\n\t\t\t\t\t\t{action fuel}\n\t\t\t\t\t\t{amount 999}\n\t\t\t\t\t}\n'
    for trig, sec, extra in [
        ('{"cheats/active/godmodecheckon"', "1", god_uc),
        ('{"cheats/active/weakenemy"', "1", ""),
        ('{"cheats/active/fuel_on"', "1.5", fuel_uc),
    ]:
        pat = re.escape(trig) + r'(\n\t\t\t\t\{condition.*?\{actions\n)'
        m = re.search(pat, txt, re.S)
        if m and '{"delay"' not in txt[m.end() : m.end() + 60]:
            txt = txt[: m.end()] + f'\t\t\t\t\t{{"delay"\n\t\t\t\t\t\t{{time {sec}}}\n\t\t\t\t\t}}\n' + extra + txt[m.end() :]

    # Verify zero Chinese characters remain
    cn_left = re.findall(r"[\u4e00-\u9fff]+", txt)
    assert not cn_left, f"Chinese still found in {label}: {cn_left[:10]}"

    # Verify balanced braces
    opens = txt.count("{")
    closes = txt.count("}")
    assert opens == closes, f"Brace mismatch in {label}: {{={opens}, }}={closes}"

    print(f"Patched {label}: addexp={ok1}, destroyarmor={ok2}, aimrange={ok3}, braces OK ({opens}), zero Chinese.")
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
\t\t{name cheat_aimrange}
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{aim_range
\t\t\t\t{scale 3}
\t\t\t}
\t\t}
\t}
\t{modifier
\t\t{name cheat_accuracy}
\t\t{filter
\t\t\t{include
\t\t\t\t{tag
\t\t\t\t\t{tag cheat_aimrange}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t{parameters
\t\t\t{accuracy
\t\t\t\t{scale 5}
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
            if nl == "cheatsmod/extension.mod":
                zout.writestr(item.filename, ext_mod.replace("\n", "\r\n").encode("utf-8"))
            elif nl == "cheatsmod/option_tags.mi":
                zout.writestr(item.filename, opt_tags.replace("\n", "\r\n").encode("utf-8"))
            elif nl in ("cheatsmod/cheats.mi", "cheatsmod/m_cheats.mi"):
                raw = zin.read(item.filename).decode("utf-8", errors="replace")
                patched = patch_mi_content(raw, item.filename)
                zout.writestr(item.filename, patched.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
    os.replace(tmp_cm, cm_pak)
    print("Rebuilt cheatsmod.pak successfully.")


if __name__ == "__main__":
    remove_chinese_docs()
    rewrite_localization()
    write_conquest_budget_files()
    rewrite_supply_and_entities()
    generate_custom_button_icons()
    rewrite_cheatsmod_pak()
    print("ALL REWORK STEPS COMPLETED!")
