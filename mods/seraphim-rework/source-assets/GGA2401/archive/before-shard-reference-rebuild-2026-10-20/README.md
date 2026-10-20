# GGA2401 — Vothuun Floating Salvo Tower

Original procedural model for Seraphim Rework, rebuilt 2026-10-20. No stock or
third-party model/texture resources were copied. The geometry and material tools
were adapted from this same mod's GGA2301 sources and are stored here independently.
The game uses only the files under `units/GGA2401`.

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

Y points up and +Z forward. Game scale is 0.1: the ground platform's source radius
19 becomes 1.9 game units, inside the retained 4×4 skirt. Five detached pointed
metal islands float above it, one gun per level. Their centres in source units are
`(-8,13,-2)`, `(7.8,25,1.5)`, `(-6.5,37,5)`, `(8,49,-4.5)`, `(-4.5,61,-5)`.
The guns are about 1.2 game units apart vertically, and every island is offset
from the central axis. Induction rings hang below the islands with clear air gaps.

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
Each muzzle is 0.1 source units ahead of its actual aperture, at game heights
1.68, 2.88, 4.08, 5.28 and 6.48 in the bind pose. The rear hinge clears the breech
above its own island deck over the full upward 0–90° pitch range. `CreateSlaver`
in the unit script copies the third gun's pitch to the other four guns while
retaining their own hinge positions. No decorative animation controls these bones.

LOD0 has 19,260 triangles / 57,780 vertex records;
LOD1 has 9,828 / 29,484. Both use the same 17-bone skeleton. Textures are
512×512 with ten mip levels. SpecTeam R/G provide metal reflection/specular;
alpha marks player-color lines and rings. Preview lighting approximates the
game's shader; it is not a screenshot from the game.

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
this visual revision preserves the entire weapon blueprint. Structural checks and
previews are separate from gameplay: no match was run for this revision, as requested.
