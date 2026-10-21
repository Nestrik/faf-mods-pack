# GGA1401 — Uya-Iava

Original experimental Seraphim power generator, added 2026-10-21.
A low open volcanic energy throat is framed by five tall, swept armor petals
of unequal height, following the stock XSB1301 silhouette. Three smaller split-
crown calderas float around it. The crater mouths and recessed field coils
are real geometry. Rounded steel shoulders, silver rolled rims,
crop-circle engravings and narrow player-color channels follow the project's
Seraphim material rules. The core turns and the islands gently float in a
16-second SCA loop. The wide platter was replaced by a smaller ring foundation
and separate rounded feet so the ground pattern remains visible.

The ground circles use the exact XSB1301 `Display.Tarmacs` setup:
`Tar12x_seraphim_01_albedo` / `_normals`, 12.8×12.8 visual decal. This does not
change the 8×8 construction skirt. The existing `SEnergyCreationUnit` base also
uses `AmbientEffects = 'ST3PowerAmbient'`: the stock rising light shafts,
expanding ground rings and distortion emitters. These activate after building,
independently of the shield toggle. Native assets are referenced through game
paths; no stock game meshes or DDS textures are redistributed.

## Rebuild

Run `generate_caldera.py` using Python with numpy and Pillow. The generator
creates two SCM LODs, SCA, three BC3 DDS maps with independently filtered data
channels, an editable OBJ/MTL, source PNG maps, a transparent construction icon,
and front/side/game-angle previews decoded from the exported SCM and DDS.
The source/export helpers are local copies of this mod's GGA2401 workflow;
GGA1401 does not import another unit's source directory at runtime or build time.
Rebuilding only writes GGA1401 outputs. Preserve a revision before changing it.

`reactor_geometry.py` contains the mesh, UV, material and software-preview tools.
`supcom_binary.py` writes SCM/SCA/BC3. `export_findings.json` records actual exported
bounds, vertex counts and DDS channel means at mip levels 0, 2, 4 and 6.
The software preview approximates lighting; it does not reproduce the engine's
environment reflections or render the live shield.
It also does not simulate the live particle emitters. When the local base-game
`env.scd` is available, `GGA1401_ground_view.png` projects the actual stock ground
decal beneath the exported SCM for layout inspection, reading its DDS directly
from that archive without extracting it into the mod.

The version before this shape correction is preserved in
`archive/before-generator-shape-2026-10-21/`, including the old runtime files and
source scripts. `reference-stock-comparison.png` is the user's in-game comparison.

## Gameplay and provisional balance

| Parameter | Value |
| --- | ---: |
| Technology | Experimental (T4), no TECH3 category |
| Energy production | 15,000/s |
| Shield upkeep | 0; full 15,000/s remains available |
| Hull | 24,000 HP |
| Shield | 6,000 HP, diameter 18, vertical offset -2 |
| Shield regeneration | 100 HP/s after 3 seconds without damage |
| Shield recharge | 25 seconds after collapse, 5 after energy depletion |
| Construction | 20,000 mass, 360,000 energy, 30,000 build points |
| Build skirt | 8×8, offsets -1.5/-1.5, same as XSB1301 |
| Ground footprint | 5×5, same as XSB1301 |
| Death explosion | 12,000 damage, radius 14, friendly damage enabled |

Construction is available to Seraphim T3 engineers, T3-capable support commanders
and ACUs with T3 engineering through standard builder categories. The shield
toggle controls only the dome; power production continues. T3 adjacency bonuses
are retained instead of inventing an unverified T4 adjacency table. The unit is
an independent build, not an upgrade or replacement for XSB1301.

The shield dimensions, costs, hull and explosion are initial balance choices.
The requested 15,000 production and T3-sized placement are fixed requirements.

## References and checks

- Local FAF `D:/Games/FAF Cache/gamedata/units.nx5`: XSB1301 footprint,
  adjacency and economy; XSB4202 shield parameters and mesh references;
  XSB2401 experimental structure armor and builder categories; XSL0309 and
  XSL0001 construction categories.
- Local `lua.nx5`: `Unit.OnStopBeingBuilt` automatically creates `Defense.Shield`;
  `EnergyCreationUnit` inherits `StructureUnit`, so no shield-specific class or
  duplicate `CreateShield` call is needed. `SEnergyCreationUnit` is the base class.
- Upstream [XSB1301](https://github.com/FAForever/fa/blob/develop/units/XSB1301/XSB1301_unit.bp)
  and [StructureUnit](https://github.com/FAForever/fa/blob/develop/lua/sim/units/StructureUnit.lua)
  were consulted alongside the local archives. Built-in paths are referenced,
  not copied into this mod.
- Materials: `ShaderName = 'Seraphim'`, team mask in Albedo.A, reflection/gloss
  in SpecTeam.R/G, normals in G/A; full channel-aware mip chains.

M28AI v327's `refCategoryPower` and `refCategoryT3Power` explicitly exclude
EXPERIMENTAL. Its Paragon filter requires MASSPRODUCTION, which this unit does
not have. Separate optional hooks recognize this ID as power and gate its
selection instead of XSB1301 behind 80 mass/s, 10,000 energy/s, 5,000 stored mass,
50% energy storage, no existing reactor and a 60-second choice cooldown. The
original selector checks CanBuild/restrictions/skirt size. Cheapest-only requests
retain stock power. The T3-only filter and the unit's real categories are kept.
See `docs/M28AI_COMPATIBILITY.md`; actual AI construction is unverified.

Status: exported files and software previews are checked separately from game
behavior. No local match has been run for this unit. In game, verify construction
menu visibility, 15,000/s economy increase, dome coverage/interception, toggle,
recharge, animation, adjacency, death explosion and the game log.
