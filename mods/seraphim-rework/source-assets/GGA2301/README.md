# GGA2301 — Ishal-Thar

General workflow, tools, format details and troubleshooting are documented in
the [local FAF modeling guide](../../../../docs/FAF_MODELING.md). Read it before
adapting this generator to another unit or mod.

The 2026-10-20 reference image is stored as `reference-2026-10-20.png`. The model
reconstructs its six plated feet, three open curved frames, floating double-point
crystal, equatorial ring and short focusing lens. Hidden sides are modeled with
radial symmetry. It is a game mesh adapted from one view, not a photogrammetry scan.

## Rebuild and editable source

Run `generate_prism_spire.py` with Python, numpy and Pillow. It writes two SCM LODs,
two SCA clips, and three 512×512 DXT5 DDS maps with mipmaps to `units/GGA2301`.
`GGA2301_source.obj` has named bone groups and an MTL file for editing in a DCC.
Source PNGs, the reference, previews and the previous working version stay here.

`prism_reference_model.py` contains the geometry, UV atlas and preview renderer.
`supcom_binary.py` contains format writers. Previews read the exported SCM back from
disk; they approximate lighting, bloom and reflections and are not game screenshots.

## Rig and coordinates

- Source coordinates are Y up and +Z forward; blueprint scale is 0.06.
- One root, `GGA2301`, parents all mechanical and decorative branches.
- `Turret` pivots at `(0, 22, 0)`. `Turret_Barrel` is its pitch child.
- `Turret_Muzzle` is a child of `Turret_Barrel`, at `(0, 0, 6.65)` locally,
  just ahead of the lens. At rest this is game height 1.32, forward offset 0.399.
- `Halo` carries the crystal; `FinLeft`, `FinRight`, `FinRear` carry the frames.
- The SCA clips key only the root and decorative branches. Aiming bones are not
  keyed, so idle animation cannot reset the weapon's yaw, pitch or muzzle.
- Activation opens the frames by 5 degrees into their modeled rest pose. Idle
  slowly rotates the crystal and bobs it by 0.12 source units over 12 seconds.

## Materials — 25 October 2026

Ishal-Thar replaces the former generic in-game name. Its original transparent
build-menu icon depicts this turret's actual silhouette and replaces the reused
stock T2 icon in both FAF icon locations. `GGA2301_icon_generated.png` was created
with the built-in imagegen tool; `icon_prompt.txt` records the prompt.
Run `prepare_icon.py` to package it as 64×64 BC3 with seven transparent mip levels.

The repainted atlas contains dark silver armor, gunmetal supports, restrained
silver edges, steel mechanisms, team-color lighting and dark metal joints.
Armor RGB is about (40,46,50), versus approximately (105,116,129) in the previous
DDS; edges are about (74,81,86). The original paired contours and nested ovals
are retained. Both LODs now use the native `Seraphim` shader, as confirmed in
locally mounted FAF `units.nx2` for XSB2301/XSB2303/XSB2401. Its `effects.nx2`
`effects/mesh.fx` reads the player mask from Albedo.A, packed normals from G/A,
and produces white emission from albedo RGB above 0.4 in PBR_Seraphim. Structural
tiles remain below that threshold; steel shine comes from material channels.

`rebuild_materials.py` rebuilds only texture maps and previews, preserving meshes,
animations and gameplay. It also remains reproducible through the full generator.
The former files are saved in `archive/before-ishal-thar-2026-10-25/`.

The material references `reference-seraphim-materials-01.png` and
`reference-seraphim-materials-02.png` show the requested stock Seraphim finish:
shiny metal with player-colored paired contours and nested oval markings.
Structural reflection/specular channels retain controlled metallic shine; armor
and support inlays use the team mask without bloom. Fine engraving is also represented
in the normal map. The large panels remain metallic between the colored lines.
SpecTeam uses R for medium-fidelity reflection, G for gloss/PBR roughness and B
for brightness/bloom. Its A is zero; Albedo.A holds player color. The crystal, light strips and flowing
armor inlays respond to player color. The crystal is faceted and opaque with the
Seraphim shader; the reference's glass transmission is approximated by shading.
The preview renderer reads the reflection channel and tangent-space normal map;
its analytic environment is illustrative and differs from the game's cubemap.
Previews now decode the exported DDS instead of source PNGs. All ten material
mip levels are decoded during this pass; channels remain present under A=0.
File checks and SCM renders were performed, but this version has not been run
in a game. Only the project working copy was updated, per the user's request.

## Export references checked on 2026-10-20

- [FAF creating-models entry](https://wiki.faforever.com/en/Development/Modding/Creating-models)
- [SupCom Blender exporter instructions](https://github.com/Oygron/SupCom_Import_Export_Blender)
- [SCM/SCA exporter source](https://github.com/Oygron/SupCom_Import_Export_Blender/blob/master/supcom-exporter.py)
- [Supreme Commander graphics study: material channels](https://www.adriancourreges.com/blog/2015/06/23/supreme-commander-graphics-study/)
- [FAF XSB2301 blueprint](https://github.com/FAForever/fa/blob/develop/units/XSB2301/XSB2301_unit.bp)

The exporter documents triangulated faces, one armature, a root named after the
unit, a bone group for every vertex, and matching animation/model bone names.
The binary writers follow its v5 header, padding, inverse bind matrix, vertex,
quaternion and frame layouts. No Blender addon was installed or executed.
The existing local BlackOpsFAF-EXUnits mesh/texture bindings were also inspected.

Game loading, material appearance, weapon tracking and activation still require
local-match confirmation; generating a preview does not establish game success.
