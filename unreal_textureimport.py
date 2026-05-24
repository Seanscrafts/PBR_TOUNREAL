import unreal
import os
import re

def get_next_sequential_number(base_name, asset_path):
    existing_assets = unreal.EditorAssetLibrary.list_assets(asset_path, recursive=False, include_folder=False)
    numbers = []
    pattern = re.compile(re.escape(base_name) + r"_(\d+)$")
    print(f"Existing assets in {asset_path}:")

    for asset in existing_assets:
        print(f" - {asset}")
        asset_name_with_extension = os.path.basename(asset)
        asset_name, _ = os.path.splitext(asset_name_with_extension)
        print(f"Asset name: {asset_name}")
        match = pattern.match(asset_name)
        if match:
            number = int(match.group(1))
            numbers.append(number)
            print(f"Found existing asset with number: {number}")

    next_number = max(numbers) + 1 if numbers else 1
    print(f"Next sequential number for '{base_name}' is {next_number}")
    return next_number


def find_latest_generation(texture_folder):
    # ComfyUI naming: TypeName_00001_.png — find the highest generation number
    numbers = []
    pattern = re.compile(r'^.+_(\d+)_\.(png|jpg|jpeg|tga)$', re.IGNORECASE)
    for filename in os.listdir(texture_folder):
        match = pattern.match(filename)
        if match:
            numbers.append(int(match.group(1)))
    if numbers:
        highest = max(numbers)
        print(f"Latest generation number: {highest}")
        return str(highest).zfill(5)
    print("No ComfyUI texture files found.")
    return None


def load_pbr_textures(texture_folder, texture_subfolder):
    generation = find_latest_generation(texture_folder)
    if not generation:
        print("No texture files found.")
        return None

    print(f"Using generation: {generation}")

    # Keys are the type names used for Unreal material parameters.
    # Values are filename prefixes ComfyUI may use (case-insensitive).
    # Note: "mask" mapped to Metalness — rename in ComfyUI if that's wrong for your workflow.
    texture_type_keywords = {
        "BaseColor":   ["basecolor", "diffuse", "albedo"],
        "ROUGHNESS":   ["roughness"],
        "NORMAL":      ["normal"],
        "Displacement":["height", "displacement", "depth"],
        "Metallic":    ["metallic", "metalness", "mask"],
    }

    textures = {k: None for k in texture_type_keywords}
    gen_suffix = f"_{generation}_"

    for filename in os.listdir(texture_folder):
        filename_lower = filename.lower()
        if gen_suffix not in filename_lower:
            continue
        if not any(filename_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tga']):
            continue

        for texture_type, keywords in texture_type_keywords.items():
            if any(filename_lower.startswith(kw + "_") for kw in keywords):
                filepath = os.path.join(texture_folder, filename)
                if texture_type == "BaseColor":
                    srgb = True
                    compression = unreal.TextureCompressionSettings.TC_DEFAULT
                    flip_green = False
                elif texture_type == "NORMAL":
                    srgb = False
                    compression = unreal.TextureCompressionSettings.TC_NORMALMAP
                    flip_green = True
                else:
                    srgb = False
                    compression = unreal.TextureCompressionSettings.TC_MASKS
                    flip_green = False
                texture_asset = import_texture(filepath, texture_subfolder, srgb=srgb, compression_settings=compression, flip_green_channel=flip_green)
                textures[texture_type] = texture_asset
                print(f"Assigned '{filename}' to '{texture_type}'")
                break

    print("Loaded textures:", textures)
    return textures


def import_texture(filepath, texture_subfolder, srgb=True, compression_settings=unreal.TextureCompressionSettings.TC_DEFAULT, flip_green_channel=False):
    texture_task = unreal.AssetImportTask()
    texture_task.filename = filepath
    texture_task.destination_path = texture_subfolder
    texture_task.replace_existing = False
    texture_task.automated = True
    texture_task.save = False

    texture_factory = unreal.TextureFactory()
    texture_task.factory = texture_factory

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([texture_task])

    if texture_task.imported_object_paths:
        imported_asset_path = texture_task.imported_object_paths[0]
        texture_asset = unreal.load_asset(imported_asset_path)

        texture_asset.set_editor_property('sRGB', srgb)
        texture_asset.set_editor_property('compression_settings', compression_settings)
        if flip_green_channel:
            texture_asset.set_editor_property('flip_green_channel', True)

        unreal.EditorAssetLibrary.save_loaded_asset(texture_asset)
        print(f"Imported texture: {imported_asset_path}")
        return texture_asset
    else:
        print(f"Failed to import texture: {filepath}")
        return None


def create_pbr_material_instance(textures, material_base_name="MI_PBR_Plane"):
    base_material_path = "/Game/3d_Material/M_PBR_Base"
    base_material = unreal.load_asset(base_material_path)
    if not base_material:
        print(f"Base material not found at {base_material_path}. Please create it manually.")
        return None

    material_instance_folder = "/Game/3d_Material/Instances"
    next_number = get_next_sequential_number(material_base_name, material_instance_folder)
    material_name = f"{material_base_name}_{next_number}"
    material_instance_path = f"{material_instance_folder}/{material_name}"
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    if unreal.EditorAssetLibrary.does_asset_exist(material_instance_path):
        print(f"Material instance '{material_name}' already exists. Skipping creation.")
        material_instance = unreal.load_asset(material_instance_path)
    else:
        material_instance = asset_tools.create_asset(
            material_name, material_instance_folder,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew()
        )
        print(f"Material instance '{material_name}' created successfully.")

    if not material_instance:
        print("Failed to create or load material instance.")
        return None

    material_instance.set_editor_property('parent', base_material)

    for param_name, texture in textures.items():
        if texture:
            set_material_instance_texture_parameter(material_instance, param_name, texture)

    set_material_instance_scalar_parameter(material_instance, "Roughnessamount", 1.0)

    unreal.EditorAssetLibrary.save_loaded_asset(material_instance)
    print(f"Material instance '{material_name}' updated successfully.")
    return material_instance


def set_material_instance_texture_parameter(material_instance, parameter_name, texture):
    success = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(material_instance, parameter_name, texture)
    if not success:
        print(f"Failed to set texture parameter '{parameter_name}' on material instance '{material_instance.get_name()}'")
    else:
        print(f"Set texture parameter '{parameter_name}' on material instance '{material_instance.get_name()}'")


def set_material_instance_scalar_parameter(material_instance, parameter_name, value):
    success = unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material_instance, parameter_name, value)
    if not success:
        print(f"Failed to set scalar parameter '{parameter_name}' on material instance '{material_instance.get_name()}'")
    else:
        print(f"Set scalar parameter '{parameter_name}' on material instance '{material_instance.get_name()}'")


def create_plane_mesh(mesh_base_name="PBR_Plane"):
    mesh_folder = "/Game/Geometry"
    next_number = get_next_sequential_number(mesh_base_name, mesh_folder)
    mesh_name = f"{mesh_base_name}_{next_number}"

    plane_path = "/Engine/BasicShapes/Plane"
    plane_asset = unreal.load_asset(plane_path)
    if not plane_asset:
        print("Plane asset not found!")
        return None

    plane_duplicate_path = f"{mesh_folder}/{mesh_name}"
    plane_asset = unreal.EditorAssetLibrary.duplicate_asset(plane_path, plane_duplicate_path)
    print(f"Plane mesh '{mesh_name}' created successfully.")

    enable_nanite_on_mesh(plane_asset)
    return plane_asset


def enable_nanite_on_mesh(mesh_asset):
    if not mesh_asset:
        print("Mesh asset is None!")
        return

    try:
        nanite_settings = unreal.MeshNaniteSettings()
        nanite_settings.enabled = True
        mesh_asset.set_editor_property('nanite_settings', nanite_settings)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh_asset)
        print(f"Nanite enabled on mesh '{mesh_asset.get_name()}'.")
    except Exception as e:
        print(f"Nanite not enabled (non-critical): {e}")


def place_mesh_in_scene(mesh_asset):
    editor_level_lib = unreal.EditorLevelLibrary
    location = unreal.Vector(0.0, 0.0, 0.0)
    rotation = unreal.Rotator(0.0, 0.0, 0.0)
    actor = editor_level_lib.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    if not actor:
        print("Failed to spawn actor.")
        return None

    static_mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    static_mesh_component.set_static_mesh(mesh_asset)

    print(f"Mesh '{mesh_asset.get_name()}' placed in the scene.")
    return actor


def assign_material_to_actor(actor, material_asset):
    if not actor or not material_asset:
        print("Actor or Material asset is None!")
        return

    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not mesh_component:
        print(f"Actor '{actor.get_name()}' does not have a StaticMeshComponent.")
        return

    mesh_component.set_material(0, material_asset)
    print(f"Material '{material_asset.get_name()}' assigned to actor '{actor.get_name()}'.")


def set_texture_object_parameter_defaults(textures):
    base_mat = unreal.load_asset('/Game/3d_Material/M_PBR_Base')
    if not base_mat:
        return
    param_map = {
        'Displacement': textures.get('Displacement'),
        'Metallic':     textures.get('Metallic'),
    }
    try:
        expressions = base_mat.get_editor_property('expressions')
        changed = False
        for expr in expressions:
            if isinstance(expr, unreal.MaterialExpressionTextureObjectParameter):
                param_name = str(expr.get_editor_property('parameter_name'))
                if param_name in param_map and param_map[param_name]:
                    expr.set_editor_property('texture', param_map[param_name])
                    print(f"Set base material default for '{param_name}'")
                    changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(base_mat)
            unreal.EditorAssetLibrary.save_loaded_asset(base_mat)
            print("M_PBR_Base recompiled with updated Displacement/Metallic defaults")
    except Exception as e:
        print(f"Could not set TextureObjectParameter defaults: {e}")


def fix_base_material_placeholder(normal_texture):
    placeholder_path = '/Game/Megascans/MSPresets/MSTextures/Placeholder_Normal'
    if unreal.load_asset(placeholder_path) is not None:
        return  # already exists and loads correctly
    if not normal_texture:
        print("No normal texture available to create placeholder — M_PBR_Base may not compile.")
        return
    source_path = normal_texture.get_path_name()
    if '.' in source_path:
        source_path = source_path.split('.')[0]
    unreal.EditorAssetLibrary.make_directory('/Game/Megascans/MSPresets/MSTextures')
    result = unreal.EditorAssetLibrary.duplicate_asset(source_path, placeholder_path)
    if result:
        print(f"Created Placeholder_Normal at {placeholder_path}")
        base_mat = unreal.load_asset('/Game/3d_Material/M_PBR_Base')
        if base_mat:
            unreal.MaterialEditingLibrary.recompile_material(base_mat)
            unreal.EditorAssetLibrary.save_loaded_asset(base_mat)
            print("M_PBR_Base recompiled successfully")
    else:
        print("Failed to create Placeholder_Normal — open M_PBR_Base and set a default normal manually")


def main():
    texture_folder = r"D:\AI\materialmaker\UnrealMats"

    if not os.path.isdir(texture_folder):
        print(f"The specified texture folder does not exist: {texture_folder}")
        return

    base_name = "MI_PBR_Plane"
    material_instance_folder = "/Game/3d_Material/Instances"
    next_number = get_next_sequential_number(base_name, material_instance_folder)

    texture_subfolder = f"/Game/3d_Material/Textures/{next_number}"
    if not unreal.EditorAssetLibrary.does_directory_exist(texture_subfolder):
        unreal.EditorAssetLibrary.make_directory(texture_subfolder)

    textures = load_pbr_textures(texture_folder, texture_subfolder)
    if not textures:
        print("Failed to load textures.")
        return

    if not textures["BaseColor"]:
        print("No base color texture found. Cannot proceed.")
        return

    fix_base_material_placeholder(textures.get("NORMAL"))
    set_texture_object_parameter_defaults(textures)

    material_instance = create_pbr_material_instance(textures, material_base_name=base_name)
    if not material_instance:
        print("Failed to create material instance.")
        return

    mesh = create_plane_mesh(mesh_base_name="PBR_Plane")
    if not mesh:
        print("Failed to create or load the plane mesh.")
        return

    actor = place_mesh_in_scene(mesh)
    if not actor:
        print("Failed to place the mesh in the scene.")
        return

    assign_material_to_actor(actor, material_instance)
    print("Process completed successfully.")


if __name__ == "__main__":
    main()
