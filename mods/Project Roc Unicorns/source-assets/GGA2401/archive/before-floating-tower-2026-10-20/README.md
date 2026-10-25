# GGA2401 — Vothuun Salvo Platform

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

Y points up and +Z forward. Game scale is 0.1: the platform's source radius 19
becomes 1.9 game units, inside a 4×4 placement skirt. The five staggered parallel
launchers share a horizontal rotating carriage and an elevating cradle.

```text
GGA2401
└── Turret                 local (0, 8, 0), yaw
    └── Turret_Barrel      local (0, 3.5, 0), pitch
        ├── Muzzle_01     local (-12, 0, 8.1)
        ├── Muzzle_02     local ( -6, 0, 10.1)
        ├── Muzzle_03     local (  0, 0, 12.1)
        ├── Muzzle_04     local (  6, 0, 10.1)
        └── Muzzle_05     local ( 12, 0, 8.1)
```

Each muzzle is 0.1 source units ahead of its actual aperture, at 1.15 game units
above ground in the bind pose. LOD0 has 8,944 triangles / 26,832 vertex records;
LOD1 has 4,744 / 14,232. Both use the same eight-bone skeleton. Textures are
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
- [Upstream XSB2303 blueprint](https://github.com/FAForever/fa/blob/develop/units/XSB2303/XSB2303_unit.bp).
- [Upstream projectile weapon state machine](https://github.com/FAForever/fa/blob/develop/lua/sim/weapons/DefaultProjectileWeapon.lua).
- Installed BlackOps `EEL0401` provides a working multi-muzzle artillery example;
  its resources are not included or required.

The old, nonworking unit blueprint/script are retained in
`archive/before-rebuild-2026-10-20/`. Structural checks and previews are separate
from gameplay: no match was run for this revision, at the user's request.
