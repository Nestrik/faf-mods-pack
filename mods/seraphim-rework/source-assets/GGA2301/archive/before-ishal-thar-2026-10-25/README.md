# GGA2301 reference rebuild

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

## Materials

The atlas contains polished silver armor, reflective gunmetal supports, chrome
edges, steel mechanisms, team-color lighting, crystal, lens and dark metal joints.
The material references `reference-seraphim-materials-01.png` and
`reference-seraphim-materials-02.png` show the requested stock Seraphim finish:
shiny metal with player-colored paired contours and nested oval markings.
Structural material reflection/specular channels are high, while the armor and
support inlays use the team mask without bloom. Fine engraving is also represented
in the normal map. The large panels remain metallic between the colored lines.
SpecTeam uses R for environment reflection, G for sunlight specular, B for
brightness/bloom and A for player color. The crystal, light strips and flowing
armor inlays respond to player color. The crystal is faceted and opaque with the
stock Unit shader; the reference's glass transmission is approximated by shading.
The preview renderer reads the reflection channel and tangent-space normal map;
its analytic environment is illustrative and differs from the game's cubemap.

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
