# STATUS — PBR Material Maker (Comfy → Unreal)

**Last updated:** 2026-05-24 (session 2)

---

## What is verified working

- All 3 CHORD workflows run and produce complete texture sets to `D:\AI\materialmaker\UnrealMats\`
- Output naming: `TypeName_00001_.png` (BaseColor, Normal, Roughness, Metalness, Displacement)
- `unreal_textureimport.py` runs to completion in the new clean project
- Run command (Unreal Output Log): `py "D:/AI/materialmaker/unreal_textureimport.py"`
- All 5 textures imported to `/Game/ImportedTextures/1/`
- `MaterialInstanceConstant` created at `/Game/Materials/MI_PBR_Plane_1`
- Plane mesh created at `/Game/Geometry/PBR_Plane_1` with Nanite enabled
- Actor placed in scene at origin, scale 400
- Metalness scalar parameter exists in M_PBR_Base (can control per-instance)

---

## Environment

| Component | Status |
|---|---|
| UE project | `D:\Docs_D\UnrealProjects\MaterialMaker\MaterialMaker.uproject` (UE 5.5, clean project) |
| Visual Studio 2022 Community | Installed with MSVC v14.44 toolset |
| UnrealMCP plugin | Compiled, connects on TCP port 55557 |
| Python MCP server | `D:\AI\unreal-mcp\Python\unreal_mcp_server.py` — registered globally |
| Old corrupted project | `D:\AI\materialmaker\Comfy_unreal_tests\` — do not open |

---

## Known issues / next session

### 1. Normal map green channel flip — FIXED
- `unreal_textureimport.py` now passes `flip_green_channel=True` for NORMAL textures automatically
- Also fixed a silent bug: the normal type check was `"Normal"` (wrong case) instead of `"NORMAL"`, so normals were getting `TC_MASKS` compression instead of `TC_NORMALMAP` — both now corrected
- Already-imported normals in existing material instances will still be wrong — re-run the import to get corrected textures

### 2. Nanite displacement — PARTIAL
- `setup_nanite_displacement.py` handles steps 1 and 2 automatically (project setting + material tessellation flag)
- Run once from Output Log: `py "D:/AI/materialmaker/setup_nanite_displacement.py"`
- Step 3 (node wiring) still needs manual work in material editor — see script output for exact steps:
  - Triplanar Displacement Result → ComponentMask(R) → Multiply(A)
  - New ScalarParameter "DisplacementAmount" (default 1.0) → Multiply(B)
  - Multiply → Displacement pin on Material Output node

### 3. Easy launcher — DONE
`Content/Python/pbr_menu.py` adds a **Tools > Import PBR Textures** menu item.
One-time setup: Edit > Project Settings > Plugins > Python > Startup Scripts → add `pbr_menu.py` → restart editor.

### 4. CHORD metalness output is pure black
CHORD is generating a flat black metalness map — not a script issue, a ComfyUI workflow issue.
- Investigate CHORD node settings / prompt for metalness in next session
- Metalness scalar in M_PBR_Base params is a good fallback in the meantime

### 5. MI texture parameter setting (save-reload fix not yet applied)
`set_material_instance_texture_parameter_value` may return False immediately after `create_asset()`.
Verify by opening `MI_PBR_Plane_1` — check if texture slots are filled or empty.
Fix (to apply to script):
```python
material_instance.set_editor_property('parent', base_material)
unreal.EditorAssetLibrary.save_loaded_asset(material_instance)
material_instance = unreal.load_asset(material_instance_path)
# then set parameters
```

---

## M_PBR_Base parameter names (confirmed)

| Slot | Script key | Material parameter name | Type |
|---|---|---|---|
| Base colour | `BaseColor` | `BaseColor` | TextureSampleParameter2D |
| Roughness | `ROUGHNESS` | `ROUGHNESS` | TextureObjectParameter → Triplanar |
| Normal | `NORMAL` | `NORMAL` | TextureSampleParameter2D |
| Displacement | `Displacement` | `Displacement` | TextureObjectParameter → Triplanar |
| Metallic | `Metallic` | `Metallic` | TextureObjectParameter → Triplanar |
| Roughness scalar | — | `Roughnessamount` | Scalar |
| Metalness scalar | — | (exists in params) | Scalar |

---

## Key file locations

| File | Path |
|---|---|
| Import script | `D:\AI\materialmaker\unreal_textureimport.py` |
| Unreal project | `D:\Docs_D\UnrealProjects\MaterialMaker\MaterialMaker.uproject` |
| ComfyUI install | `D:\AI\ComfyUI_windows_portable\ComfyUI\` |
| Workflow (text prompt) | `D:\AI\materialmaker\Texturemaker_CHORD.json` |
| Workflow (img2pbr) | `D:\AI\materialmaker\Texturemaker_CHORD_img2pbr.json` |
| Workflow (img2pbr seamless) | `D:\AI\materialmaker\Texturemaker_CHORD_img2pbr_seamless.json` |
| Texture output folder | `D:\AI\materialmaker\UnrealMats\` |
| Master material | `Content/3d_Material/M_PBR_Base.uasset` |
| Triplanar function | `Content/3d_Material/MaterialFunctions/MF_VTA_Triplanar.uasset` |

## Key models (ComfyUI)

| Model | Location |
|---|---|
| `flux1-dev-fp8.safetensors` | `models\unet\` |
| `clip_l.safetensors` + `t5xxl_fp8_e4m3fn.safetensors` | `models\clip\` |
| `ae.safetensors` | `models\vae\` |
| `chord_v1.safetensors` | `models\checkpoints\` |
