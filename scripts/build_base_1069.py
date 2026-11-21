import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

GOH = r"D:\SteamLibrary\steamapps\common\Call to Arms - Gates of Hell"
WS = r"D:\SteamLibrary\steamapps\workshop\content\400750"

MODS_DIR = os.path.join(GOH, "mods")
CHEAT_SRC = os.path.join(WS, "3113216568")
MACE_SRC = os.path.join(WS, "2905667604")
BM_COMPAT_SRC = os.path.join(WS, "3642867748")

CHEAT_OUT = os.path.join(MODS_DIR, "cheatsmod_26_1069_fix")
COMPAT_OUT = os.path.join(MODS_DIR, "bm_everything_stays_mace_compat")


def build_cheatsmod():
    print("=== Building cheatsmod_26_1069_fix ===")
    if os.path.exists(CHEAT_OUT):
        shutil.rmtree(CHEAT_OUT)
    os.makedirs(CHEAT_OUT, exist_ok=True)

    # 1. Copy base files/folders from original CheatsMod 2.6 (except multi.pak, single.pak, interface.pak, mod.info)
    for item in os.listdir(CHEAT_SRC):
        src = os.path.join(CHEAT_SRC, item)
        dst = os.path.join(CHEAT_OUT, item)
        if item == "mod.info":
            continue
        elif item == "resource":
            os.makedirs(dst, exist_ok=True)
            for sub in os.listdir(src):
                sub_src = os.path.join(src, sub)
                sub_dst = os.path.join(dst, sub)
                if sub == "interface.pak":
                    continue
                elif sub == "map":
                    os.makedirs(sub_dst, exist_ok=True)
                    # Copy cheatsmod.pak only; we rebuild multi.pak and single.pak fresh from 1.069 + MACE
                    shutil.copy2(
                        os.path.join(sub_src, "cheatsmod.pak"),
                        os.path.join(sub_dst, "cheatsmod.pak"),
                    )
                elif os.path.isdir(sub_src):
                    shutil.copytree(sub_src, sub_dst)
                else:
                    shutil.copy2(sub_src, sub_dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # 2. Write updated mod.info
    mod_info = """{mod
\t{name "CheatsMod 2.6 (1.069 + Conquest Fix)"}
\t{tags "Mod"}
\t{desc "CheatsMod 2.6 updated for game v1.069.0 & MACE. Fixes missing menu and keeps the cheat menu persistent after all Conquest waves are called in."}
\t{minGameVersion "1.069.0"}
\t{maxGameVersion "any"}
}
"""
    with open(os.path.join(CHEAT_OUT, "mod.info"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(mod_info)

    # 3. Build updated interface.pak with fresh 1.069 SceneGameView.xml + original CheatsMod icons
    with zipfile.ZipFile(os.path.join(GOH, "resource", "interface", "interface.pak"), "r") as zb:
        base_xml = zb.read("layout/views/scene/SceneGameView.xml").decode("utf-8")

    # Insert independent cheat_reinforcement_layer outside unitspawn_layer
    anchor = '<DialogRef refid="ui_replay_control" skin="default_skin"/>\r\n\t\t\t\t\t\t</Children>\r\n\t\t\t\t\t</FlowPanel>'
    if anchor not in base_xml:
        anchor = '<DialogRef refid="ui_replay_control" skin="default_skin"/>\n\t\t\t\t\t\t</Children>\n\t\t\t\t\t</FlowPanel>'
    assert anchor in base_xml, "Anchor not found in base SceneGameView.xml!"

    cheat_panel = (
        anchor
        + '\r\n\t\t\t\t\t<FlowPanel id="cheat_reinforcement_layer" direction="vertical" halign="right" valign="top" gap="8" justify="false" enableif="(game.campaign or game.multiplayer) and !game.cooperative and !game.singleplayer and !gui.editor">'
        + '\r\n\t\t\t\t\t\t<Insets right="20" top="90"/>'
        + '\r\n\t\t\t\t\t\t<Children>'
        + '\r\n\t\t\t\t\t\t\t<DialogRef refid="gui_gc_reinforcement"/>'
        + '\r\n\t\t\t\t\t\t</Children>'
        + '\r\n\t\t\t\t\t</FlowPanel>'
    )
    patched_xml = base_xml.replace(anchor, cheat_panel, 1)

    # Validate XML well-formedness
    ET.fromstring(patched_xml.encode("utf-8"))
    print("  Validated patched 1.069 SceneGameView.xml successfully.")

    out_iface_pak = os.path.join(CHEAT_OUT, "resource", "interface.pak")
    with zipfile.ZipFile(os.path.join(CHEAT_SRC, "resource", "interface.pak"), "r") as zin, \
         zipfile.ZipFile(out_iface_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.lower() == "interface/layout/views/scene/scenegameview.xml":
                zout.writestr("interface/layout/views/scene/SceneGameView.xml", patched_xml.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
    print(f"  Built {out_iface_pak}")

    # 4. Collect all fresh 1.069 .mi files from Base + DLCs, then overlay MACE's multi.pak .mi files
    multi_mi = {}   # path relative to resource/map/ (e.g. multi/...) -> bytes
    single_mi = {}  # path relative to resource/map/ (e.g. single/...) -> bytes

    def collect_from_pak(pak_path, rel_root):
        with zipfile.ZipFile(pak_path, "r") as z:
            for name in z.namelist():
                if not name.lower().endswith(".mi"):
                    continue
                # Normalize VFS path under resource/
                vfs = (rel_root + "/" + name if rel_root else name).replace("\\", "/")
                vfs_lower = vfs.lower()
                if vfs_lower.startswith("map/multi/"):
                    key = vfs[4:]  # strip "map/"
                    multi_mi[key.lower()] = (key, z.read(name))
                elif vfs_lower.startswith("map/single/"):
                    key = vfs[4:]
                    single_mi[key.lower()] = (key, z.read(name))

    # Scan base game + DLCs
    res_dir = os.path.join(GOH, "resource")
    for root, dirs, files in os.walk(res_dir):
        for f in sorted(files):
            if f.endswith(".pak"):
                p = os.path.join(root, f)
                rel = os.path.relpath(root, res_dir).replace(os.sep, "/")
                if rel == ".":
                    rel = ""
                try:
                    collect_from_pak(p, rel)
                except zipfile.BadZipFile:
                    pass

    base_multi_count = len(multi_mi)
    base_single_count = len(single_mi)

    # Overlay MACE's multi.pak .mi files so MACE's 16 frontlines missions are preserved!
    mace_multi_pak = os.path.join(MACE_SRC, "resource", "map", "multi.pak")
    mace_overlaid = 0
    with zipfile.ZipFile(mace_multi_pak, "r") as z:
        for name in z.namelist():
            if name.lower().endswith(".mi") and name.lower().startswith("multi/"):
                multi_mi[name.lower()] = (name, z.read(name))
                mace_overlaid += 1

    print(f"  Collected {base_multi_count} base+DLC multi .mi ({mace_overlaid} overlaid from MACE), {base_single_count} single .mi")

    def inject_cheat_include(raw_bytes):
        txt = raw_bytes.decode("utf-8", errors="replace")
        if 'cheatsmod/cheats.mi' in txt.lower():
            return raw_bytes
        # Insert right after first {mission line
        lines = txt.splitlines(keepends=True)
        inserted = False
        out_lines = []
        for line in lines:
            out_lines.append(line)
            if not inserted and line.strip().lower().startswith("{mission"):
                eol = "\r\n" if line.endswith("\r\n") else "\n"
                out_lines.append(f'(include "/map/cheatsmod/cheats.mi"){eol}')
                inserted = True
        if not inserted:
            out_lines.insert(0, '(include "/map/cheatsmod/cheats.mi")\r\n')
        return "".join(out_lines).encode("utf-8")

    out_multi_pak = os.path.join(CHEAT_OUT, "resource", "map", "multi.pak")
    with zipfile.ZipFile(out_multi_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for k in sorted(multi_mi.keys()):
            orig_name, data = multi_mi[k]
            zout.writestr(orig_name, inject_cheat_include(data))
    print(f"  Built {out_multi_pak} ({len(multi_mi)} maps)")

    out_single_pak = os.path.join(CHEAT_OUT, "resource", "map", "single.pak")
    with zipfile.ZipFile(out_single_pak, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for k in sorted(single_mi.keys()):
            orig_name, data = single_mi[k]
            zout.writestr(orig_name, inject_cheat_include(data))
    print(f"  Built {out_single_pak} ({len(single_mi)} maps)")


def build_entitymanager_compat():
    print("=== Building bm_everything_stays_mace_compat ===")
    if os.path.exists(COMPAT_OUT):
        shutil.rmtree(COMPAT_OUT)
    set_dir = os.path.join(COMPAT_OUT, "resource", "set")
    os.makedirs(set_dir, exist_ok=True)

    # Read BM Mod - MACE Compat Patch's entitymanager.set (which already has MACE's special entities + BM Mod's limbs + higher debris limits)
    bm_em_path = os.path.join(BM_COMPAT_SRC, "resource", "set", "entitymanager.set")
    with open(bm_em_path, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()

    # Apply Everything Stays - MACE's 9999 limits to dead, stuff, equip (and raise limbs to 1000)
    replacements = [
        ('{group "dead" actor dead\n\t\t(mod "mp" \t\t{limit 200})\n\t\t(mod not "mp"\t{limit 200})',
         '{group "dead" actor dead\n\t\t(mod "mp" \t\t{limit 9999})\n\t\t(mod not "mp"\t{limit 9999})'),
        ('{group "limbs" gameentity\n\t\t(mod "mp" \t\t{limit 500})\n\t\t(mod not "mp"\t{limit 500})',
         '{group "limbs" gameentity\n\t\t(mod "mp" \t\t{limit 1000})\n\t\t(mod not "mp"\t{limit 1000})'),
        ('{group "stuff" stuff\n\t\t(mod "mp" \t\t{limit 100})\n\t\t(mod not "mp"\t{limit 200})',
         '{group "stuff" stuff\n\t\t(mod "mp" \t\t{limit 9999})\n\t\t(mod not "mp"\t{limit 9999})'),
        ('{group "equip" stuff\n\t\t(mod "mp" \t\t{limit 100})\n\t\t(mod not "mp"\t{limit 100})',
         '{group "equip" stuff\n\t\t(mod "mp" \t\t{limit 9999})\n\t\t(mod not "mp"\t{limit 9999})'),
    ]
    txt_norm = txt.replace("\r\n", "\n")
    for old, new in replacements:
        assert old in txt_norm, f"Expected block not found in BM entitymanager.set:\n{old}"
        txt_norm = txt_norm.replace(old, new, 1)

    with open(os.path.join(set_dir, "entitymanager.set"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(txt_norm)

    mod_info = """{mod
\t{name "BM Mod + Everything Stays - MACE Compat"}
\t{tags "Mods"}
\t{desc "Merges entitymanager.set from BM Mod - MACE Compat Patch and Everything Stays - MACE so bodies, weapons, equipment, severed limbs, and MACE special entities all work together."}
\t{minGameVersion "any"}
\t{maxGameVersion "any"}
}
"""
    with open(os.path.join(COMPAT_OUT, "mod.info"), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(mod_info)
    print(f"  Built {COMPAT_OUT}")


if __name__ == "__main__":
    build_cheatsmod()
    build_entitymanager_compat()
    print("ALL DONE!")
