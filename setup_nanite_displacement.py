"""
Run once from the Unreal Output Log:
    py "D:/AI/materialmaker/setup_nanite_displacement.py"

Does steps 1 and 2 of the Nanite displacement setup automatically.
Step 3 (node wiring) must be done manually in the material editor — see printed instructions.
"""

import unreal


def enable_nanite_tessellation_setting():
    # Apply at runtime immediately
    unreal.SystemLibrary.execute_console_command(None, "r.Nanite.Tessellation 1")
    print("Nanite tessellation enabled for this session.")

    # Make it persist across restarts via DefaultEngine.ini
    ini_path = unreal.Paths.project_config_dir() + "DefaultEngine.ini"
    section = "[/Script/Engine.RendererSettings]"
    key = "r.Nanite.Tessellation"
    entry = f"{key}=1"

    try:
        with open(ini_path, "r") as f:
            content = f.read()

        if entry in content:
            print(f"DefaultEngine.ini already has {entry} — skipping.")
            return

        if section in content:
            content = content.replace(section, f"{section}\n{entry}")
        else:
            content += f"\n{section}\n{entry}\n"

        with open(ini_path, "w") as f:
            f.write(content)

        print(f"DefaultEngine.ini updated: {entry} added under {section}")
    except Exception as e:
        print(f"Could not update DefaultEngine.ini automatically: {e}")
        print(f"Add this line manually under {section} in DefaultEngine.ini:")
        print(f"    {entry}")


def enable_tessellation_on_material():
    mat_path = "/Game/3d_Material/M_PBR_Base"
    mat = unreal.load_asset(mat_path)
    if not mat:
        print(f"Could not load material at {mat_path}")
        return

    # Try UE5 Nanite tessellation property — name may vary by engine version
    tried = []
    for prop in ["d3d11_tessellation_mode", "tessellation_mode"]:
        try:
            mat.set_editor_property(prop, unreal.MaterialTessellationMode.MTM_FLAT_TESSELLATION)
            unreal.MaterialEditingLibrary.recompile_material(mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mat)
            print(f"Material tessellation enabled on M_PBR_Base (property: {prop})")
            return
        except Exception as e:
            tried.append(f"{prop}: {e}")

    print("Could not set tessellation mode via Python. Manual fallback:")
    print("  Open M_PBR_Base → Details panel → check 'Tessellation'")
    for t in tried:
        print(f"  Tried: {t}")


def print_manual_wiring_steps():
    print("\n--- STEP 3: Manual node wiring (do this in the material editor) ---")
    print("Open M_PBR_Base in the material editor, then:")
    print("  1. Locate the Displacement triplanar output (Result pin of MF_VTA_Triplanar for Displacement)")
    print("  2. Add a ComponentMask node — enable R channel only")
    print("  3. Connect: Triplanar Result → ComponentMask")
    print("  4. Add a ScalarParameter node, name it 'DisplacementAmount', default 1.0")
    print("  5. Add a Multiply node")
    print("  6. Connect: ComponentMask → Multiply(A), DisplacementAmount → Multiply(B)")
    print("  7. Connect: Multiply → Displacement pin on the Material Output node")
    print("  8. Apply and save")
    print("-------------------------------------------------------------------\n")


def main():
    print("=== Nanite Displacement Setup ===")
    enable_nanite_tessellation_setting()
    enable_tessellation_on_material()
    print_manual_wiring_steps()
    print("Steps 1 and 2 complete. Follow the printed instructions for step 3.")


if __name__ == "__main__":
    main()
