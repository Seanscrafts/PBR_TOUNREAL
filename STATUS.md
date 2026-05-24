# STATUS — PBR Material Maker (Comfy → Unreal)

**Last updated:** 2026-05-24 (session 4)

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
- `unreal_textureimport.py` passes `flip_green_channel=True` for NORMAL textures automatically
- Normal type check corrected to `"NORMAL"` — textures now get `TC_NORMALMAP` compression

### 2. Nanite displacement — FIXED (confirmed by Sean)
- Nanite working in the project
- `setup_nanite_displacement.py` handles project settings and material tessellation flag

### 3. Easy launcher — DONE
`Content/Python/pbr_menu.py` adds a **Tools > Import PBR Textures** menu item.
One-time setup: Edit > Project Settings > Plugins > Python > Startup Scripts → add `pbr_menu.py` → restart editor.

### 4. CHORD metalness output — FIXED (by Sean in ComfyUI)
Metalness map was pure black — fixed directly in the ComfyUI workflow.

### 5. MI texture parameter save-reload fix — APPLIED (session 3)
`set_material_instance_texture_parameter_value` can return False immediately after `create_asset()` because the freshly created UObject isn't fully initialised.
Fix applied to `unreal_textureimport.py`: after setting the parent material, the script now saves and reloads the MI before setting texture parameters.

### 6. Independent X/Y tiling — DEFERRED to next session
- M_PBR_Base confirmed: BaseColor, Metallic, Roughness, Displacement all go through MF_VTA_Triplanar. NORMAL goes direct.
- All triplanar instances share a single `TILE SIZE` scalar — independent X/Y not possible with current setup.
- Triplanar switch script attempted but reverted (M_PBR_Base restored from backup). `set_texture_object_parameter_defaults()` also removed from import script (used protected `expressions` API).
- **Plan for next session:** Reverse-engineer Unreal Sensei master material (owned by Sean) and rebuild for UE 5.5. His version supports local-space triplanar and many other features. Better foundation than patching current M_PBR_Base.
- Backup of original M_PBR_Base lives at `/Game/3d_Material/M_PBR_Base_BACKUP` — keep it.

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
