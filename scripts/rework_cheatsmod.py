import os
import re
import zipfile

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
        "Set to player0": "Switch active player if cheats don't affect your units.\nCurrent Player: <e(shadow)><c(ffffff)>0</c></e>",
        "Set to player1": "Switch active player if cheats don't affect your units.\nCurrent Player: <e(shadow)><c(ff0000)>1</c></e>",
        "Set to player2": "Switch active player if cheats don't affect your units.\nCurrent Player: <e(shadow)><c(00d319)>2</c></e>",
        "Set to player3": "Switch active player if cheats don't affect your units.\nCurrent Player: <e(shadow)><c(f2c200)>3</c></e>",
        "Deploy mines": "AT Mines (x8)",
        "Lay a mine field": "Spawn 8 armed Anti-Tank mines at cursor",
        "Fast Miner": "Fast Mine Engineer",
        "Fast Miner hint": "Spawn Engineer with 40 fast AT + 40 fast AP mines (Hold Shift to queue minefields!)",
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

    # Insert Fast Miner tags before final '}'
    for idx in range(len(out) - 1, -1, -1):
        if out[idx].strip() == "}":
            out.insert(idx, '\t{"Fast Miner" "Fast Mine Engineer"}')
            out.insert(idx + 1, '\t{"Fast Miner hint" "Spawn Engineer with 40 fast AT + 40 fast AP mines (Hold Shift to queue!)"}')
            break

    result = "\r\n".join(out) + "\r\n"
    assert not re.search(r"[\u4e00-\u9fff]", result), "Chinese still found in singlecheats.pot!"
    with open(pot_path, "w", encoding="utf-8", newline="") as f:
        f.write(result)
    print("Rewrote singlecheats.pot in pure English.")


def rewrite_supply_and_entities():
    # 1. Clean lightweight MACE-compatible cheat_supply.inc (no FPS kill!)
    supply_inc = """(include "/properties/resupply.inc")

(define "cheat_supply_ammo"
\t{extender "supply_zone"
\t\t{fuel \t{amount 5}\t{value 1}}
\t\t{resupply
\t\t\t("items_light_generic")
\t\t\t("items_light_ger")
\t\t\t("items_light_rus")
\t\t\t("items_light_eng")
\t\t\t("items_light_usa")
\t\t\t("items_light_fin")
\t\t\t("items_light_jap")
\t\t\t("items_light_fra")
\t\t\t("items_heavy_generic")
\t\t\t("items_heavy_ger")
\t\t\t("items_heavy_rus")
\t\t\t("items_heavy_eng")
\t\t\t("items_heavy_fin")
\t\t\t("items_heavy_usa")
\t\t\t("items_heavy_jap")
\t\t\t("items_heavy_fra")
\t\t\t("items_explosives")
\t\t\t("items_engineer")
\t\t\t("items_medic")
\t\t}
\t\t{radius\t\t\t\t30}
\t\t{resupplyPeriod\t\t3}
\t\t{regenerationPeriod 0}
\t\t{limit\t\t\t\t0}
\t}
\t{DecalView supply_zone
\t\t{Sprite "supply_zone.ebm"
\t\t\t{Visibility 0.25}
\t\t}
\t\t{Layer grounddynamic}
\t\t{Visible 0}
\t}
)

(define "cheat_supply_ammo_global"
\t{extender "supply_zone"
\t\t{fuel \t{amount 10}\t{value 1}}
\t\t{resupply
\t\t\t("items_light_generic")
\t\t\t("items_light_ger")
\t\t\t("items_light_rus")
\t\t\t("items_light_eng")
\t\t\t("items_light_usa")
\t\t\t("items_light_fin")
\t\t\t("items_light_jap")
\t\t\t("items_light_fra")
\t\t\t("items_heavy_generic")
\t\t\t("items_heavy_ger")
\t\t\t("items_heavy_rus")
\t\t\t("items_heavy_eng")
\t\t\t("items_heavy_fin")
\t\t\t("items_heavy_usa")
\t\t\t("items_heavy_jap")
\t\t\t("items_heavy_fra")
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

    # 2. Update entity.pak: instant-plant mines with cheat_mine tag + ammo_cheatsmod_global
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
\t{tags "cheat_mine"}
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
\t{tags "cheat_mine"}
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
\t{props "no_recrew_logic"}
\t{tags "cheatsmod_inf-ammo"}
\t("cheat_supply_ammo_global")
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
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag _user}}
\t\t\t\t\t\t\t\t\t\t}}
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
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/active/addexp"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_auto_detect_player_trigger():
    """Auto-detects the actual human player slot (0-7) via _user tag or autoassign probe."""
    user_checks = []
    probe_checks = []
    for p in range(8):
        user_checks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type entities}}
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag _user}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
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
        probe_checks.append(f"""\t\t\t\t\t{{"if"
\t\t\t\t\t\t{{condition
\t\t\t\t\t\t\t{{type entities}}
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{ignore_captured_by_user 0}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{include
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_player_probe}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t\t{{player "{p}"}}
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
\t\t\t\t\t\t{{time 1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"spawn"
\t\t\t\t\t\t{{entity "ammo_cheatsmod_global"}}
\t\t\t\t\t\t{{waypoint "30001"}}
\t\t\t\t\t\t{{tag cheat_player_probe}}
\t\t\t\t\t}}
\t\t\t\t\t{{"autoassign"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{tag cheat_player_probe}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.2}}
\t\t\t\t\t}}
{chr(10).join(probe_checks)}
\t\t\t\t\t{{"delete"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{tag cheat_player_probe}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 3}}
\t\t\t\t\t}}
{chr(10).join(user_checks)}
\t\t\t\t}}
\t\t\t}}"""


def make_repair_trigger():
    comps = ["body", "turret", "gun", "engine", "trackleft", "trackright", "wheel", "shield", "mantlet", "cabin"]
    blocks = []
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
\t\t\t\t\t{{"trigger"
\t\t\t\t\t\t{{name "cheats/destroyarmor"}}
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t}}"""


def make_aimrange_trigger():
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
\t\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
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
\t\t\t\t\t{{"spawn"
\t\t\t\t\t\t{{entity "mp/ger/early/elite_rifle"}}
\t\t\t\t\t\t{{waypoint "30001"}}
\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t}}
\t\t\t\t\t{{"delay"
\t\t\t\t\t\t{{time 0.1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine m1a1_cheat"}}
\t\t\t\t\t\t{{amount 40}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine s_cheat"}}
\t\t\t\t\t\t{{amount 40}}
\t\t\t\t\t}}
\t\t\t\t\t{{"inventory"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{action add}}
\t\t\t\t\t\t{{item "mine_detector"}}
\t\t\t\t\t\t{{amount 1}}
\t\t\t\t\t}}
\t\t\t\t\t{{"actor_state"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{control user}}
\t\t\t\t\t\t{{human
\t\t\t\t\t\t\t{{veterancy 8}}
\t\t\t\t\t\t\t{{stamina 100}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
{chr(10).join(player_assign)}
\t\t\t\t\t{{"entity_state"
\t\t\t\t\t\t{{selector
\t\t\t\t\t\t\t{{source advanced}}
\t\t\t\t\t\t\t{{group
\t\t\t\t\t\t\t\t{{select
\t\t\t\t\t\t\t\t\t{{tag
\t\t\t\t\t\t\t\t\t\t{{tag cheat_fast_miner}}
\t\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t\t{{tag_add cheat_delete}}
\t\t\t\t\t\t{{tag_remove cheat_fast_miner}}
\t\t\t\t\t}}
\t\t\t\t\t{{"event"
\t\t\t\t\t\t{{event "cheats/fast_miner"}}
\t\t\t\t\t\t{{mode reset}}
\t\t\t\t\t\t{{delay 0}}
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
\t\t\t\t{text "Instant Win (Conquest)"}
\t\t\t\t{image "whitesnoop/cheats/enabled"}
\t\t\t\t{hint "Immediately win the current Conquest battle"}
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

    # 4. Add cheat_miner reinforcement button right after cheat_mine_ap button
    if '{"cheat_miner"' not in txt:
        miner_btn = """\t\t\t{"cheat_miner"
\t\t\t\t{state hidden}
\t\t\t\t{text "Fast Mine Engineer"}
\t\t\t\t{image "whitesnoop/menus/infantry"}
\t\t\t\t{hint "mission/singlecheats/Fast Miner hint"}
\t\t\t\t{count -1}
\t\t\t\t{score 0}
\t\t\t\t{delay 0}
\t\t\t\t{eventStart "cheat_click"}
\t\t\t\t{eventEnd "cheats/fast_miner"}
\t\t\t}"""
        txt = txt.replace(
            '\t\t\t{"cheat_mine"\n',
            miner_btn + '\n\t\t\t{"cheat_mine"\n',
            1,
        )

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

    # 7. Initialize cheat_options-player$ = 0 in cheats/set/vars
    if '{var "cheat_options-player$"}' not in txt[:16000]:
        txt = txt.replace(
            '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_infammo$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}',
            '\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_infammo$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}\n\t\t\t\t\t{"set_i"\n\t\t\t\t\t\t{var "cheat_options-player$"}\n\t\t\t\t\t\t{op "="}\n\t\t\t\t\t\t{value 0}\n\t\t\t\t\t}',
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

    # 9. Upgrade cheats/units/mine and cheats/units/mine_ap to spawn 8 mines per click
    old_mine_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_antitank_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t}"""
    if txt.count(old_mine_spawn) == 4:
        txt = txt.replace(old_mine_spawn, old_mine_spawn + "\n" + old_mine_spawn)

    old_mine_ap_spawn = """\t\t\t\t\t{"spawn"
\t\t\t\t\t\t{entity "mine_s_cheat"}
\t\t\t\t\t\t{waypoint "30001"}
\t\t\t\t\t}"""
    if txt.count(old_mine_ap_spawn) == 4:
        txt = txt.replace(old_mine_ap_spawn, old_mine_ap_spawn + "\n" + old_mine_ap_spawn)

    # Faster arming in minegetsfilled (0.2s instead of 1s)
    txt = txt.replace(
        '\t\t\t{"minegetsfilled"\n\t\t\t\t{"delay"\n\t\t\t\t\t{time 1}\n\t\t\t\t}',
        '\t\t\t{"minegetsfilled"\n\t\t\t\t{"delay"\n\t\t\t\t\t{time 0.2}\n\t\t\t\t}',
        1,
    )

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

    # 11. Add {delay 1} to continuous triggers (godmodecheckon, weakenemy, fuel_on) so they don't run 60x/sec!
    for trig, sec in [
        ('{"cheats/active/godmodecheckon"', "1"),
        ('{"cheats/active/weakenemy"', "1"),
        ('{"cheats/active/fuel_on"', "1.5"),
    ]:
        pat = re.escape(trig) + r'(\n\t\t\t\t\{condition.*?\{actions\n)'
        m = re.search(pat, txt, re.S)
        if m and '{"delay"' not in txt[m.end() : m.end() + 60]:
            txt = txt[: m.end()] + f'\t\t\t\t\t{{"delay"\n\t\t\t\t\t\t{{time {sec}}}\n\t\t\t\t\t}}\n' + txt[m.end() :]

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
    rewrite_cheatsmod_pak()
    print("ALL REWORK STEPS COMPLETED!")
