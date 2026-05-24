import unreal

src = '/Game/3d_Material/M_PBR_Base_BACKUP'
dst = '/Game/3d_Material/M_PBR_Base'

if not unreal.EditorAssetLibrary.does_asset_exist(src):
    print("ERROR: No backup found at M_PBR_Base_BACKUP.")
else:
    if unreal.EditorAssetLibrary.does_asset_exist(dst):
        deleted = unreal.EditorAssetLibrary.delete_asset(dst)
        if not deleted:
            print("ERROR: Could not delete current M_PBR_Base. Close the material editor first.")
            raise SystemExit
        print("Deleted current M_PBR_Base.")

    result = unreal.EditorAssetLibrary.duplicate_asset(src, dst)
    if result:
        unreal.EditorAssetLibrary.save_loaded_asset(unreal.load_asset(dst))
        print("M_PBR_Base restored from backup.")
    else:
        print("ERROR: Restore failed.")
