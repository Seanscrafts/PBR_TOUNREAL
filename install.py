from pathlib import Path
import json
import os
import shutil
import sys


REPO_DIR = Path(__file__).parent
CONFIG_PATH = REPO_DIR / "config.json"
WORKFLOWS_DIR = REPO_DIR / "workflows"
UNREAL_IMPORT_SCRIPT = REPO_DIR / "unreal_textureimport.py"
PBR_MENU_SCRIPT = REPO_DIR / "pbr_menu.py"


def ask_existing_project_path():
    project_path = Path(input(r"Enter the full path to your Unreal project folder (e.g. C:\UnrealProjects\MyProject): ").strip().strip('"'))
    if not project_path.exists() or not project_path.is_dir():
        print("ERROR: Unreal project folder does not exist.")
        sys.exit(1)
    return project_path


def ask_texture_output_folder():
    texture_path = Path(input(r"Enter the full path where ComfyUI should save textures (e.g. C:\MyTextures\UnrealMats): ").strip().strip('"'))
    if not texture_path.exists():
        answer = input(f"Texture output folder does not exist. Create it? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("ERROR: Texture output folder does not exist.")
            sys.exit(1)
        texture_path.mkdir(parents=True, exist_ok=True)
    return texture_path


def write_config(texture_output_folder, ue_python_dir):
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    config["texture_output_folder"] = str(texture_output_folder)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=2)
        config_file.write("\n")

    ue_python_dir.mkdir(parents=True, exist_ok=True)
    with (ue_python_dir / "config.json").open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=2)
        config_file.write("\n")


def walk_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_nodes(child)


def patch_workflows(texture_output_folder):
    if not WORKFLOWS_DIR.exists():
        return

    for workflow_path in sorted(WORKFLOWS_DIR.glob("*.json")):
        with workflow_path.open("r", encoding="utf-8") as workflow_file:
            workflow = json.load(workflow_file)

        patched_count = 0
        for node in walk_nodes(workflow):
            if node.get("title") in ("Output Folder", "Output Folder Path"):
                widgets_values = node.get("widgets_values")
                if isinstance(widgets_values, list) and widgets_values:
                    widgets_values[0] = str(texture_output_folder)
                    patched_count += 1

        with workflow_path.open("w", encoding="utf-8") as workflow_file:
            json.dump(workflow, workflow_file, indent=2)
            workflow_file.write("\n")

        print(f"{workflow_path.name}: patched {patched_count} node(s)")


def copy_files(ue_python_dir):
    ue_python_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(UNREAL_IMPORT_SCRIPT, ue_python_dir / "unreal_textureimport.py")
    if PBR_MENU_SCRIPT.exists():
        shutil.copy2(PBR_MENU_SCRIPT, ue_python_dir / "pbr_menu.py")
    else:
        print(f"WARNING: Skipping missing file: {PBR_MENU_SCRIPT}")
    shutil.copy2(CONFIG_PATH, ue_python_dir / "config.json")


def main():
    project_path = ask_existing_project_path()
    texture_output_folder = ask_texture_output_folder()
    ue_python_dir = project_path / "Content" / "Python"

    write_config(texture_output_folder, ue_python_dir)
    patch_workflows(texture_output_folder)
    copy_files(ue_python_dir)

    print("""
✓ Install complete.

Next steps:
1. Open Unreal Engine and load your project.
2. Go to Edit > Project Settings > Plugins > Python > Startup Scripts
   Add: pbr_menu.py
3. Drag a workflow JSON from the 'workflows/' folder onto ComfyUI.
4. Rebuild the UnrealMCP plugin if prompted.
""")


if __name__ == "__main__":
    main()
