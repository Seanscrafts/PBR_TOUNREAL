"""
Adds a "Import PBR Textures" item to the Unreal Tools menu.

One-time setup:
  1. Edit > Project Settings > Plugins > Python
  2. Under "Startup Scripts", add:  pbr_menu.py
  3. Restart the editor

After that, Tools > Import PBR Textures runs the pipeline every time.
"""

import unreal


def register_pbr_menu():
    menus = unreal.ToolMenus.get()
    tools_menu = menus.find_menu("LevelEditor.MainMenu.Tools")
    if not tools_menu:
        print("PBR menu: could not find LevelEditor Tools menu.")
        return

    tools_menu.add_section("PBRPipeline", unreal.Text("PBR Pipeline"))

    entry = unreal.ToolMenuEntry(
        name="PBRImportTextures",
        type=unreal.MultiBlockType.MENU_ENTRY,
    )
    entry.set_label(unreal.Text("Import PBR Textures"))
    entry.set_tool_tip(unreal.Text("Import latest ComfyUI textures and create material instance in Unreal"))
    entry.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON,
        "",
        "D:/AI/materialmaker/unreal_textureimport.py",
    )
    tools_menu.add_menu_entry("PBRPipeline", entry)
    menus.refresh_all_widgets()
    print("PBR Pipeline: 'Import PBR Textures' added to Tools menu.")


register_pbr_menu()
