# Thuunar T1 missile carrier

Original model rebuild, 21 October 2026. The unit keeps ID `GGA0101` and its
combat/economic parameters. The stock XSL0111 was read locally to study its
inclined open launch cradle and bone contract. No stock mesh, texture or animation
is included in this export. `stock_reference_*.png` are local study renders from
the installed game's SCM/DDS, not screenshots or source assets for redistribution.

## Design and files

The new T1 chassis has two short caterpillar pods, four exposed road wheels per
side at LOD0, a low central hull and a small rear engine cover. It omits the T2
carrier's broad third prow/track, large curved shoulders and aerial-like tail fins.
The launcher is a newly constructed pair of rounded, tapered guide leaves around
a separate launchable missile, inclined 30 degrees. Silver-steel material and
thin player-color crop-circle lines follow the current Seraphim project style.

- `generate_t1_launcher.py`: geometry, bind pose, reload, wreck, icons and build.
- `launcher_geometry.py`: local mesh/atlas/SCM preview utilities, adapted from the
  project's GGA2401 tools; independent of the artillery generator at build time.
- `supcom_binary.py`: SCM/SCA/BC3 writers; extends the local writer with rotated
  bind poses and full inverse world bind matrices.
- `GGA0101_source.obj/.mtl`: editable geometry, UVs, normals and named bone groups.
- `GGA0101_*_source.png`: editable material maps; actual game maps are DDS.
- `GGA0101_views.png`, individual views and `GGA0101_lod1.png`: exported-file views.
- `GGA0101_wreck.png`: approximate lit render of the exported damaged model.
- `model_stats.json`: exported triangle/vertex counts for both intact/wreck LODs.
- `archive/before-t1-chassis-2026-10-21`: previous blueprint, script and icons.

Run from the repository root with the Python path in `docs/FAF_MODELING.md`:

```powershell
& $modelPython 'mods\Project Roc Unicorns\source-assets\GGA0101\generate_t1_launcher.py'
```

`--skip-textures` reuses material maps; `--skip-previews` skips render/icon output.
The generator writes only this unit's runtime assets and its source directory.
Material maps use 512×512 BC3 DDS with independent-channel mipmaps down to 1×1.
Albedo.A contains the team mask; SpecTeam.R/G contain reflection/gloss, B emission;
packed normals use G/A with neutral values about 128. No alpha-premultiplication
is applied to these material data maps. Transparent build icons use normal alpha
filtering and are written to both existing icon directories.

## Rig

Y is up, +Z forward; blueprint scale is 0.1. Source coordinates:

| Bone | Parent | Local position | Rotation |
| --- | --- | --- | --- |
| GGA0101 | none | 0, 0, 0 | identity |
| Turret | GGA0101 | 0, 3.65, -2.7 | -30 degrees about X |
| missile | Turret | 0, 0, 9 | identity |

Missile nose/emission position in the rest pose is `(0, 8.15, 5.0942)` source
units, or `(0, 0.815, 0.5094)` game units. Its +Z axis points up/forward at
30 degrees. Rocket geometry belongs only to `missile`, so the stock weapon's
`HideMuzzle` can hide it on firing. The launch cradle belongs to `Turret`; all
chassis parts belong to the root. The non-turreted stock weapon is retained.

The 2.3333333-second reload SCA contains root and Turret only, preserving local
translations and gently dipping the cradle by 7 degrees before returning exactly
to bind pose. It does not key the muzzle bone, which also receives native rack
recoil. The quaternion/inverse-bind convention was checked against all three
stock XSL0111 bones, with maximum matrix component difference below 0.000001.

## Explicit destroyed model

`props/GGA0101_wreck` contains a normal reclaimable `Wreckage` prop, its own mesh
blueprint, two damaged SCM LODs and a scorched albedo. A collapsed hull, displaced
track pod, lowered/broken cradle and loose guide fragment distinguish it from
the live model. Its static skeleton has one root (`GGA0101_wreck`), so no intact
reload pose is required. Normals are shared from the unit atlas; the `Wreckage`
shader uses FAF's stock wreckage-noise texture by reference.

The unit's Wreckage.Blueprint names this prop and `UseCustomMesh = true` preserves
its own mesh. This follows the mounted local `lua/wreckage.lua`, CreateWreckage:
it sets the unit's scale, assigns reclaim amounts, and only substitutes
Display.MeshBlueprintWrecked when UseCustomMesh is false/nil. Destruction effects
and standard conditions remain native: excessive overkill and other normal FAF
rules can suppress a wreck, and a surviving wreck can take damage.

The old unit depended on the stock mesh generated while processing another unit.
`lua/system/Blueprints.lua`, ExtractWreckageBlueprint, returns without creating a
wreck mesh if that referenced mesh has not yet been registered. This is a plausible
cause of the reported invisible wreck; the actual game log was not available.
The explicit prop removes that dependency without changing global FAF hooks.

## Verification boundaries

File checks cover SCM layout, finite vertices, index ranges, triangle areas,
normalized tangent basis, bone links and inverse binds, matching LOD skeletons,
SCA local poses/quaternions, material channels and all decoded mip levels, and
runtime resource paths. Previews read exported SCM/DDS with backface culling and
multiple player colors. They approximate lighting and are not in-game screenshots.

No game was launched. In a local match, verify construction and scale, movement,
rocket disappearance/reload, missile direction, destruction, visible wreck and
engineer reclaim; inspect the log for mesh/animation errors. The working mod has
not been copied into the installed mod directory by this change.

Local sources: installed `gamedata/units.scd` XSL0111 model and animation;
FAF `units.nx2` XSL0111 script; mounted `lua.nx2` `lua/system/Blueprints.lua`,
`lua/wreckage.lua`, `lua/sim/Unit.lua`; stock `props.scd` DefaultWreckage prop;
the project modeling guide and GGA2401 material/render tools.
