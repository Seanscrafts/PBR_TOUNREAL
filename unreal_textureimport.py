"""
PBR Material Maker — Unreal import script
Project: BlendMasterMaterial (UE 5.7)
Master material: M_BlendMaster_Nanite

Run from UE Output Log:
    py "D:/AI/materialmaker/unreal_textureimport.py"

Picks up the latest CHORD texture set from D:/AI/materialmaker/UnrealMats/,
imports all 5 maps, creates a material instance from M_BlendMaster_Nanite.
"""

import unreal
import json
import os
import re
import sys
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

config_path = Path(__file__).parent / "config.json"
try:
    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("ERROR: Run install.py first to configure your paths.")
    sys.exit(1)

if not config.get("texture_output_folder"):
    print("ERROR: Run install.py first to configure your paths.")
    sys.exit(1)

TEXTURE_FOLDER      = config["texture_output_folder"]
MASTER_MATERIAL     = config["master_material_path"]
MI_FOLDER           = config["mi_folder"]
TEXTURE_BASE_FOLDER = config["texture_base_folder"]
MI_BASE_NAME        = config["mi_base_name"]

# Map from M_BlendMaster_Nanite Layer A texture param names to CHORD filename prefixes
TEXTURE_PARAMS = {
    "Albedo Color A": {
        "keywords": ["basecolor", "diffuse", "albedo"],
        "srgb": True,
        "compression": unreal.TextureCompressionSettings.TC_DEFAULT,
        "flip_green": False,
    },
    "Normal A": {
        "keywords": ["normal"],
        "srgb": False,
        "compression": unreal.TextureCompressionSettings.TC_NORMALMAP,
        "flip_green": True,
    },
    "Roughness A": {
        "keywords": ["roughness"],
        "srgb": False,
        "compression": unreal.TextureCompressionSettings.TC_MASKS,
        "flip_green": False,
    },
    "Metallic A": {
        "keywords": ["metallic", "metalness", "mask"],
        "srgb": False,
        "compression": unreal.TextureCompressionSettings.TC_MASKS,
        "flip_green": False,
    },
    "Height A": {
        "keywords": ["height", "displacement", "depth"],
        "srgb": False,
        "compression": unreal.TextureCompressionSettings.TC_MASKS,
        "flip_green": False,
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_next_sequential_number(base_name, asset_path):
    existing = unreal.EditorAssetLibrary.list_assets(asset_path, recursive=False, include_folder=False)
    numbers = []
    pattern = re.compile(re.escape(base_name) + r"_(\d+)$")
    for asset in existing:
        name = os.path.splitext(os.path.basename(asset))[0]
        m = pattern.match(name)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers) + 1 if numbers else 1


def pick_generation(folder):
    pattern = re.compile(r'^.+_(\d+)_\.(png|jpg|jpeg|tga)$', re.IGNORECASE)
    sets = {}
    for f in os.listdir(folder):
        m = pattern.match(f)
        if m:
            num = m.group(1)
            sets[num] = sets.get(num, 0) + 1

    if not sets:
        unreal.log_error("No texture sets found in " + folder)
        return None

    sorted_nums = sorted(sets.keys(), key=lambda x: int(x))

    if len(sorted_nums) == 1:
        unreal.log(f"One set found, using: {sorted_nums[0]}")
        return sorted_nums[0]

    import tkinter as tk

    labels = [f"Set {n}  —  {sets[n]} maps" for n in sorted_nums]
    selected = [None]

    root = tk.Tk()
    root.title("Select PBR Set")
    root.geometry("320x220")
    root.lift()
    root.attributes("-topmost", True)

    tk.Label(root, text="Choose a PBR set to import:", pady=8).pack()

    listbox = tk.Listbox(root, selectmode=tk.SINGLE, width=40)
    for label in labels:
        listbox.insert(tk.END, label)
    listbox.select_set(len(labels) - 1)
    listbox.pack(fill=tk.BOTH, expand=True, padx=12)
    listbox.bind('<Double-Button-1>', lambda e: on_ok())
    listbox.bind('<Return>', lambda e: on_ok())

    def on_ok():
        sel = listbox.curselection()
        if sel:
            selected[0] = sorted_nums[sel[0]]
        root.destroy()

    def on_cancel():
        root.destroy()

    frame = tk.Frame(root)
    frame.pack(pady=8)
    tk.Button(frame, text="Import", width=10, command=on_ok).pack(side=tk.LEFT, padx=6)
    tk.Button(frame, text="Cancel", width=10, command=on_cancel).pack(side=tk.LEFT, padx=6)

    root.mainloop()

    if selected[0] is None:
        unreal.log("Import cancelled.")
        return None

    unreal.log(f"Selected set: {selected[0]}")
    return selected[0]

# ── Import ────────────────────────────────────────────────────────────────────

def import_texture(filepath, dest_folder, srgb, compression, flip_green):
    task = unreal.AssetImportTask()
    task.filename = filepath
    task.destination_path = dest_folder
    task.replace_existing = False
    task.automated = True
    task.save = False
    task.factory = unreal.TextureFactory()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    if not task.imported_object_paths:
        unreal.log_error(f"Import failed: {filepath}")
        return None

    tex = unreal.load_asset(task.imported_object_paths[0])
    tex.set_editor_property('sRGB', srgb)
    tex.set_editor_property('compression_settings', compression)
    if flip_green:
        tex.set_editor_property('flip_green_channel', True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    unreal.log(f"Imported: {os.path.basename(filepath)} → {tex.get_name()}")
    return tex


def load_pbr_textures(folder, dest_folder):
    generation = pick_generation(folder)
    if not generation:
        return None

    gen_suffix = f"_{generation}_"
    textures = {k: None for k in TEXTURE_PARAMS}

    for filename in os.listdir(folder):
        fl = filename.lower()
        if gen_suffix not in fl:
            continue
        if not any(fl.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tga']):
            continue
        for param_name, cfg in TEXTURE_PARAMS.items():
            if any(fl.startswith(kw + "_") for kw in cfg["keywords"]):
                tex = import_texture(
                    os.path.join(folder, filename), dest_folder,
                    cfg["srgb"], cfg["compression"], cfg["flip_green"]
                )
                textures[param_name] = tex
                unreal.log(f"  '{filename}' → param '{param_name}'")
                break

    missing = [k for k, v in textures.items() if v is None]
    if missing:
        unreal.log_warning(f"Missing textures: {missing}")
    return textures

# ── Material instance ─────────────────────────────────────────────────────────

def create_material_instance(textures, slot_number):
    base_mat = unreal.load_asset(MASTER_MATERIAL)
    if not base_mat:
        unreal.log_error(f"Master material not found: {MASTER_MATERIAL}")
        return None

    mi_name = f"{MI_BASE_NAME}_{slot_number:02d}"
    mi_path = f"{MI_FOLDER}/{mi_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        unreal.log(f"MI already exists, loading: {mi_path}")
        mi = unreal.load_asset(mi_path)
    else:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            mi_name, MI_FOLDER,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew()
        )
        unreal.log(f"Created MI: {mi_path}")

    if not mi:
        unreal.log_error("Failed to create material instance.")
        return None

    mi.set_editor_property('parent', base_mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    mi = unreal.load_asset(mi_path)  # reload after parent set

    for param_name, tex in textures.items():
        if tex:
            ok = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param_name, tex)
            if ok:
                unreal.log(f"  Set '{param_name}'")
            else:
                unreal.log_warning(f"  Failed to set '{param_name}'")

    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log(f"MI ready: {mi_path}")
    return mi

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.isdir(TEXTURE_FOLDER):
        unreal.log_error(f"Texture folder not found: {TEXTURE_FOLDER}")
        return

    slot = get_next_sequential_number(MI_BASE_NAME, MI_FOLDER)
    tex_dest = f"{TEXTURE_BASE_FOLDER}/{slot:02d}"

    for folder in [MI_FOLDER, tex_dest]:
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.make_directory(folder)

    unreal.log(f"=== BlendMaster Import — slot {slot:02d} ===")

    textures = load_pbr_textures(TEXTURE_FOLDER, tex_dest)
    if not textures or not textures.get("Albedo Color A"):
        unreal.log_error("No BaseColor texture found. Aborting.")
        return

    mi = create_material_instance(textures, slot)
    if not mi:
        return

    unreal.log(f"=== Done. MI: {MI_FOLDER}/{MI_BASE_NAME}_{slot:02d} ===")


main()
