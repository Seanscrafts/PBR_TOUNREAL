import unreal

src = '/Game/3d_Material/M_PBR_Base'
dst = '/Game/3d_Material/M_PBR_Base_BACKUP'

if unreal.EditorAssetLibrary.does_asset_exist(dst):
    print(f"Backup already exists at {dst} — delete it first if you want a fresh backup.")
else:
    result = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
    if result:
        unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(dst))
        print(f"Backup saved at {dst}")
    else:
        print("ERROR: Backup failed.")
