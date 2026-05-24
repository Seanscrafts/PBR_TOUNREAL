import unreal

MAT_PATH = '/Game/3d_Material/M_PBR_Base'
BACKUP_PATH = '/Game/3d_Material/M_PBR_Base_BACKUP'

def add_triplanar_switch():
    if not unreal.EditorAssetLibrary.does_asset_exist(BACKUP_PATH):
        print("ERROR: No backup found at M_PBR_Base_BACKUP. Run backup_base_material.py first.")
        return

    material = unreal.load_asset(MAT_PATH)
    if not material:
        print("ERROR: Could not load M_PBR_Base.")
        return

    mel = unreal.MaterialEditingLibrary
    bx, by = 1200, -800

    # --- Shared UV scaling chain ---
    tiling_x = mel.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, bx, by)
    tiling_x.set_editor_property('parameter_name', 'TilingX')
    tiling_x.set_editor_property('default_value', 1.0)

    tiling_y = mel.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, bx, by + 120)
    tiling_y.set_editor_property('parameter_name', 'TilingY')
    tiling_y.set_editor_property('default_value', 1.0)

    append = mel.create_material_expression(
        material, unreal.MaterialExpressionAppendVector, bx + 250, by + 60)
    mel.connect_material_expressions(tiling_x, '', append, 'A')
    mel.connect_material_expressions(tiling_y, '', append, 'B')

    texcoord = mel.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, bx + 250, by - 120)
    texcoord.set_editor_property('coordinate_index', 0)

    uv_multiply = mel.create_material_expression(
        material, unreal.MaterialExpressionMultiply, bx + 500, by)
    mel.connect_material_expressions(texcoord, '', uv_multiply, 'A')
    mel.connect_material_expressions(append,   '', uv_multiply, 'B')

    print("Created UV scaling chain: TexCoord * (TilingX, TilingY)")

    # --- Per-channel: TextureSampleParameter2D (UV path) + StaticSwitchParameter ---
    #
    # New texture params are named with _UV suffix to avoid collision with the
    # existing TextureObjectParameter nodes (ROUGHNESS, Metallic, Displacement).
    # The import script will be updated to set both names.
    #
    # connect_material_property() REPLACES the existing connection on that pin,
    # so after this runs the triplanar output is disconnected from Roughness/Metallic/Displacement.
    # Open M_PBR_Base and drag each triplanar result into its Switch.True pin manually.
    #
    # MP_DISPLACEMENT is the Nanite displacement pin (UE 5.4+).
    # If the material errors on save, the Displacement switch won't work — skip it and wire manually.

    # MP_DISPLACEMENT does not exist in UE 5.5 Python API — Displacement wired manually.
    channels = [
        ('ROUGHNESS_UV',    unreal.MaterialProperty.MP_ROUGHNESS,  bx + 750, by - 400),
        ('Metallic_UV',     unreal.MaterialProperty.MP_METALLIC,    bx + 750, by),
        ('Displacement_UV', None,                                    bx + 750, by + 400),
    ]

    for uv_name, mat_prop, cx, cy in channels:
        tex_param = mel.create_material_expression(
            material, unreal.MaterialExpressionTextureSampleParameter2D, cx, cy + 200)
        tex_param.set_editor_property('parameter_name', uv_name)
        mel.connect_material_expressions(uv_multiply, '', tex_param, 'Coordinates')

        switch = mel.create_material_expression(
            material, unreal.MaterialExpressionStaticSwitchParameter, cx + 300, cy)
        switch.set_editor_property('parameter_name', 'UseTriplanar')
        switch.set_editor_property('default_value', True)

        mel.connect_material_expressions(tex_param, 'RGB', switch, 'False')

        if mat_prop is not None:
            try:
                mel.connect_material_property(switch, '', mat_prop)
                print(f"  [{uv_name}] Created and wired to material output.")
            except Exception as e:
                print(f"  [{uv_name}] WARNING: Could not wire to material output: {e}")
                print(f"  [{uv_name}] Wire the Switch output manually.")
        else:
            print(f"  [{uv_name}] MANUAL: wire Switch output to material's Displacement pin.")

        print(f"  [{uv_name}] MANUAL: drag existing triplanar output for this channel → Switch.True")

    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)

    print("\nDone. M_PBR_Base recompiled and saved.")
    print("Open M_PBR_Base and make the 3 Switch.True connections from the existing triplanar outputs.")
    print("Then run your import script — ROUGHNESS_UV / Metallic_UV / Displacement_UV will be set automatically.")

add_triplanar_switch()
