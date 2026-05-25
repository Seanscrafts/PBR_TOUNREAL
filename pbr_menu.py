"""
Adds Tools > Import PBR Textures menu item.

One-time setup:
  Edit > Project Settings > Plugins > Python > Startup Scripts
  Add: pbr_menu.py
  Restart editor.
"""

import unreal
import traceback
import os

def register_menu():
    try:
        menus = unreal.ToolMenus.get()
        tools_menu = menus.find_menu("LevelEditor.MainMenu.Tools")

        if not tools_menu:
            unreal.log_error("pbr_menu: Could not find Tools menu.")
            return

        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unreal_textureimport.py").replace("\\", "/")

        entry = unreal.ToolMenuEntry(
            name="ImportPBRTextures",
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
        )
        entry.set_label(unreal.Text("Import PBR Textures"))
        entry.set_tool_tip(unreal.Text("Import latest CHORD texture set from UnrealMats/ into 3dTextures/"))
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.COMMAND,
            "",
            f'py "{script_path}"'
        )
        tools_menu.add_menu_entry("PBRTools", entry)
        menus.refresh_all_widgets()
        unreal.log("pbr_menu: SUCCESS — Tools > Import PBR Textures registered.")

    except Exception as e:
        unreal.log_error("pbr_menu FAILED: " + str(e))
        unreal.log_error(traceback.format_exc())

register_menu()
