# GGA2401 — Vothuun Floating Salvo Tower

Original procedural model for Seraphim Rework, rebuilt 2026-10-21. No stock or
third-party model/texture resources were copied. The geometry and material tools
were adapted from this same mod's GGA2301 sources and are stored here independently.
The game uses the files under `units/GGA2401` and the two standard unit-icon
locations. The latest appearance follows the user's `reference-floating-shards.png`
and `reference-artillery-shape.png`, refined by the user's 2026-10-21 request for
smooth rounded Seraphim shapes and brighter metallic surfaces. These are visual
references, not game textures. See [the stock-model investigation](stock-seraphim-study.md).

## Regenerate

Run `generate_salvo_platform.py` with Python, numpy and Pillow. It overwrites only
GGA2401's two SCMs, three DDS textures and source/preview outputs. It does not
change the unit/mesh blueprints or script. Blender is not required.

```powershell
& 'C:\Users\Nestr\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'mods\seraphim-rework\source-assets\GGA2401\generate_salvo_platform.py'
```

`artillery_geometry.py` contains mesh primitives, the material atlas and an SCM
reader/renderer. `supcom_binary.py` writes SCM v5 and BC3/DXT5 DDS with mipmaps.
The OBJ/MTL preserve editable geometry, UVs, normals and named rigid bone groups;
the full rig is defined in the generator. No SCA is needed: the weapon owns aiming.

## Dimensions and rig

Y points up and +Z forward. Game scale is 0.1: the ground petals reach 18.7 source
units from the centre, inside the retained 4×4 skirt. Five detached pointed
metal islands float above it, one gun per level. Their centres in source units are
`(-8,13,-2)`, `(7.8,25,1.5)`, `(-6.5,37,5)`, `(8,49,-4.5)`, `(-4.5,61,-5)`.
The guns are about 1.2 game units apart vertically, and every island is offset
from the central axis. Islands retain tapered keels and satellites but now use
curved profiles and rounded tips. Ground petals and split weapon leaves have
smoothed outlines, volumetric rolled edges and consistent interpolated normals.
The long silhouettes remain recognizable without the old faceted cuts.

```text
GGA2401
└── Turret                       local (0,0,0), common yaw
    ├── Island_01                local centre as listed above
    │   └── Barrel_01            local (0,3.8,-4), pitch slave
    │       └── Muzzle_01        local (0,0,14.1)
    ├── Island_02 → Barrel_02 → Muzzle_02
    ├── Island_03 → Turret_Barrel → Muzzle_03   master pitch
    ├── Island_04 → Barrel_04 → Muzzle_04
    └── Island_05 → Barrel_05 → Muzzle_05
```

The last four branches use the same local hinge/muzzle offsets as the first.
Each muzzle is just ahead of its split-blade firing channel, at game heights
1.68, 2.88, 4.08, 5.28 and 6.48 in the bind pose. The rear hinge clears the breech
above its own island deck over the full upward 0–90° pitch range. `CreateSlaver`
in the unit script copies the third gun's pitch to the other four guns while
retaining their own hinge positions. No decorative animation controls these bones.

LOD0 has 27,085 triangles / 54,129 vertex records;
LOD1 has 12,993 / 25,353. Both retain the same 17-bone skeleton and firing positions.
Textures are 1024×1024 BC3/DXT5 with eleven mip levels. Slightly brighter steel
and stronger metallic reflection/gloss follow the stock Seraphim shader contract.
`ShaderName = 'Seraphim'` uses the approved crop-circle mask in **Albedo.A**;
the former SpecTeam-alpha mask was transferred with all 1,048,576 pixels intact.
`seraphim_inlays` itself is unchanged. Normal maps are now packed in G/A as read
by native `ComputeNormal`; the previous opaque RGB packing was incorrect.
Broad armor panels retain planar UVs so concentric circles stay legible.
The guns have smoothly curved breeches, rolled armor leaves, a long split tip and
an open central channel. `GGA2401_island_closeup.png` renders the exported SCM's
third island and gun for detailed inspection. Preview lighting approximates the
game's shader; it is not a screenshot from the game.

## Unique unit icon

`GGA2401_icon_generated.png` is the original transparent artwork produced with
the built-in image_gen tool; the exact prompt is in `icon-prompt.txt`. It uses the
five staggered jagged islands, split-blade weapons, pointed petal base and green
crop-circle markings as a recognizable construction-menu silhouette. The PNG is
stored here, independently of the image tool's default output directory.

Run `prepare_icon.py` to resample this artwork to 64×64 and encode seven BC3/DXT5
mip levels into both `icons/units/GGA2401_icon.dds` and
`textures/ui/common/icons/units/GGA2401_icon.dds`. Alpha is preserved. The decoded
game DDS is enlarged without smoothing in `GGA2401_icon_game_preview.png` for
small-size review. The standard strategic artillery symbol is unchanged.

## Weapon and balance

See the mod README and `units/GGA2401/GGA2401_unit.bp`. A single stock artillery
weapon has a ten-entry muzzle list, with each muzzle repeated twice, and a
0.2-second delay. Thus there are ten shots, not five independent weapon clocks.
`MuzzleSalvoSize = 10` and `RackRecoilDistance = 0` satisfy FAF's delayed-salvo
initialization rule. `RenderFireClock` and `RateOfFire` provide the native reload
indicator and nominal 40-second cycle. `RackSalvoReloadTime` remains zero as on
the stock T2 artillery; engine rate limiting provides the cooldown.

Baseline sources inspected:

- Local `D:\Games\FAF Cache\gamedata\units.nx5`: `units/XSB2303/XSB2303_unit.bp`
  and script; T3 engineer/SACU construction filters.
- Local `lua.nx5`: `lua/sim/weapons/DefaultProjectileWeapon.lua` and the
  `SIFZthuthaamArtilleryCannon` weapon class.
- Local `units.nx5`: `units/UAL0205/UAL0205_script.lua` and its blueprint show
  `CreateSlaver(self, slaveBone, masterBone)` for a second barrel following the
  weapon-controlled barrel. This tower adapts that pattern for four slaves.
- [Upstream XSB2303 blueprint](https://github.com/FAForever/fa/blob/develop/units/XSB2303/XSB2303_unit.bp).
- [Upstream projectile weapon state machine](https://github.com/FAForever/fa/blob/develop/lua/sim/weapons/DefaultProjectileWeapon.lua).
- Installed BlackOps `EEL0401` provides a working multi-muzzle artillery example;
  its resources are not included or required.

The old, nonworking unit blueprint/script are retained in
`archive/before-rebuild-2026-10-20/`. The working low five-gun platform, including
all runtime files, generators, source OBJ/textures and previews, is saved in
`archive/before-floating-tower-2026-10-20/`. The user praised its firing mechanics;
the former saucer-island tower and its icons are saved under
`archive/before-shard-reference-rebuild-2026-10-20/`. The last angular model and
all its source files are preserved in `archive/before-rounded-seraphim-2026-10-21/`.
This revision preserves the unit blueprint and aiming script byte for byte;
mesh shader/materials and geometry have changed. The existing unique icon is retained.
Structural checks and
previews are separate from gameplay: no match was run for this revision, as requested.
