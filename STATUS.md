# STATUS — PBR Material Maker (Comfy → Unreal)

**Last updated:** 2026-05-25 (session 6)

---

## Active project

**Migrated to UE 5.7 + BlendMasterMaterial project.**
Old UE 5.5 project (`MaterialMaker`) is superseded. Do not use it as reference.

| Component | Status |
|---|---|
| UE project | `D:\Docs_D\UnrealProjects\BlendMasterMaterial\BlendMasterMaterial.uproject` (UE 5.7) |
| Visual Studio 2022 Community | Installed |
| UnrealMCP plugin | Compiled for UE 5.7, running on TCP 55557 ✓ |
| Python MCP server | `D:\AI\unreal-mcp\Python\unreal_mcp_server.py` — needs re-registration to new project |
| Old project (UE 5.5) | `D:\Docs_D\UnrealProjects\MaterialMaker\MaterialMaker.uproject` — archived, do not open |

---

## What is verified working (session 6)

- Tools > Import PBR Textures menu item working in UE 5.7 ✓
  - Registered via `pbr_menu.py` in `Content/Python/` + `DefaultEngine.ini` startup script
  - Fixed UE 5.7 API break: `find_or_add_section` removed, `ToolMenuStringCommandType.COMMAND` used
- `unreal_textureimport.py` updated:
  - Material instances now named `MI_3dmaterial_01`, `MI_3dmaterial_02`, etc.
  - Plane creation and actor spawn removed — script creates MI only, nothing placed in level

---

## UE 5.7 plugin fixes applied (session 5)

Three breaking changes from UE 5.5 → 5.7, all patched in the plugin source:

| File | Fix |
|---|---|
| `UnrealMCPBlueprintCommands.cpp` | `ANY_PACKAGE` → `FindFirstObject<UClass>(..., EFindFirstObjectOptions::None)` (4 calls) |
| `UnrealMCPBlueprintNodeCommands.cpp` | Same `ANY_PACKAGE` fix (5 calls) |
| `MCPServerRunnable.cpp` | `TCHAR_TO_UTF8` macro → `FTCHARToUTF8` class; global `BufferSize` renamed to `RecvBufferSize` (C4459 error) |

Fixed source is live in both:
- `D:\Docs_D\UnrealProjects\BlendMasterMaterial\Plugins\UnrealMCP\Source\`
- `D:\AI\unreal-mcp\MCPGameProject\Plugins\UnrealMCP\Source\` (synced back)

---

## Next task

**Package the pipeline for distribution** — so others can install it without a D drive or ComfyUI.

Key design questions to resolve at session start:
- Config file for paths (texture folder, UE project dir) — user-editable, not hardcoded
- ComfyUI optional or required? (currently required for texture generation)
- Distribution format: installer script, zip + README, or something else
- Where does the UE plugin live in the package?

Steps remaining:
1. [ ] **Next:** Design distribution format and path config approach
2. [ ] Extract hardcoded paths from `unreal_textureimport.py` into a config file
3. [ ] Extract hardcoded paths from `pbr_menu.py` into same config
4. [ ] Write install script (sets up folders, copies files to UE Content/Python)
5. [ ] Test clean install on a machine without existing project setup
6. [ ] Re-register Python MCP server to new project path (separate task)

---

## BlendMasterMaterial master materials

Location: `Content/SenseiMaterials/Materials/`

| Asset | Use |
|---|---|
| `M_BlendMaster` | Standard (non-Nanite) master |
| `M_BlendMaster_Nanite` | **Primary target** — Nanite-enabled master |
| `M_BlendMaster_VT` | Virtual Texture variant |
| `M_BlendMaster_Nanite_VT` | Nanite + Virtual Texture variant |

**Layer A parameter names (confirmed):**

| CHORD output | M_BlendMaster_Nanite param | Compression |
|---|---|---|
| BaseColor / albedo | `Albedo Color A` | TC_DEFAULT, sRGB |
| Normal | `Normal A` | TC_NORMALMAP, flip green |
| Roughness | `Roughness A` | TC_MASKS |
| Metallic / metalness | `Metallic A` | TC_MASKS |
| Height / displacement | `Height A` | TC_MASKS |

Also available (not wired to CHORD): `Ambient Occlusion A`, `MaskORM A`, `Height Blend A`
Useful scalars per layer: `Size A` (tiling), `Roughness Strength A`, `Normal Strength A`, `Displacement Amount A`
Independent X/Y tiling via Vector param `Tiling A` (X=tileX, Y=tileY) — built in to this material.

---

## Key file locations

| File | Path |
|---|---|
| Import script | `D:\AI\materialmaker\unreal_textureimport.py` |
| UE menu script | `D:\Docs_D\UnrealProjects\BlendMasterMaterial\Content\Python\pbr_menu.py` |
| Inspect script | `D:\Docs_D\UnrealProjects\BlendMasterMaterial\Content\Python\inspect_blend_master.py` |
| UE project | `D:\Docs_D\UnrealProjects\BlendMasterMaterial\BlendMasterMaterial.uproject` |
| ComfyUI install | `D:\AI\ComfyUI_windows_portable\ComfyUI\` |
| Workflow (text prompt) | `D:\AI\materialmaker\Texturemaker_CHORD.json` |
| Workflow (img2pbr) | `D:\AI\materialmaker\Texturemaker_CHORD_img2pbr.json` |
| Workflow (img2pbr seamless) | `D:\AI\materialmaker\Texturemaker_CHORD_img2pbr_seamless.json` |
| Texture output folder | `D:\AI\materialmaker\UnrealMats\` |

## Key models (ComfyUI)

| Model | Location |
|---|---|
| `flux1-dev-fp8.safetensors` | `models\unet\` |
| `clip_l.safetensors` + `t5xxl_fp8_e4m3fn.safetensors` | `models\clip\` |
| `ae.safetensors` | `models\vae\` |
| `chord_v1.safetensors` | `models\checkpoints\` |
