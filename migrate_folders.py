"""
One-time migration: moves existing assets into /Game/3d_Material/

Run once from the Unreal Output Log:
    py "D:/AI/materialmaker/migrate_folders.py"

Moves:
    /Game/ImportedTextures/  ->  /Game/3d_Material/Textures/
    /Game/Materials/         ->  /Game/3d_Material/Instances/

Unreal handles redirectors automatically so existing references stay valid.
Safe to run again — skips folders that don't exist.
"""

import unreal

lib = unreal.EditorAssetLibrary

MOVES = [
    ("/Game/ImportedTextures", "/Game/3d_Material/Textures"),
    ("/Game/Materials",        "/Game/3d_Material/Instances"),
]

for src, dst in MOVES:
    if not lib.does_directory_exist(src):
        print(f"Skipping '{src}' — does not exist.")
        continue

    if lib.does_directory_exist(dst):
        print(f"Destination '{dst}' already exists — merging contents.")

    print(f"Moving '{src}' -> '{dst}' ...")
    result = lib.rename_directory(src, dst)
    if result:
        print(f"  Done.")
    else:
        print(f"  Failed — check Output Log for details.")

print("Migration complete. You can delete this script when done.")
