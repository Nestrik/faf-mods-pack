# GGA0402 — Itha-Suun

Separate experimental hover tank copied from GGA0401, modeled from the user's
annotated concept on 22 October 2026. GGA0402 is now included in **Seraphim Additional Units**; GGA0401 remains in
Seraphim Rework. The mods are independent. Build with Seraphim T3 engineers or a commander with T3 engineering.
Sandbox spawn ID: `gga0402`.

## Concept and geometry

`reference-concept.png` preserves the drawing. The left drawing is treated as a
top view with the front at the top: an open double rail, two central circular
gun hardpoints, scalloped starboard armor, detached fore-left petal, smaller
port islands and four AA turrets. The right drawing supplies the main gun's
elongated spindle casing and spiral bands; the lower-right sketch supplies its
three-petal muzzle. Unshown underside details and mount heights are interpreted.

The two newly modeled main pods have rounded armor, physical helical ribs,
player-color veins and open focusing petals. The rear pod is raised for neutral
forward firing clearance. Gaps are real empty space; four separate hull sections
have gentle 8-second drift. Their AA guns are parented to their platforms.

LOD0 occupies **3.951×5.935** horizontally, Y=0.33–2.475 game units before the
inherited 0.4 hover elevation. The collision/mesh height is 2.6 to fit the rear
gun. Footprint, skirt and selection dimensions remain 4×6. Source scale is 0.1.
There are **24 bones**. Main yaw/pitch/muzzle branches are separate; native
`CreateSlaver` copies front yaw/pitch rotations to the rear assembly, retaining
its own pivots. Neutral muzzle positions in source units: `(0,15,21.5)` and
`(0,21,2.5)`. Both shots use the shared target's firing solution. All-angle,
all-pitch and terrain clearance still require game verification.

LOD0: **24,560 vertices / 36,556 triangles**; LOD1: **13,244 / 17,766**. Skeletons
match and both fit SCM's 16-bit indices. Native `Seraphim` materials use Albedo.A
player color, SpecTeam reflection/gloss and G/A packed normals. Each DDS has ten
independently downsampled mip levels. No stock model or texture is copied.

`GGA0402_hull_top.png` hides the main pods to expose the two attachment circles,
matching the sketch. Plan views put the prow up and port left. `GGA0402_top.png`
includes both pods; `GGA0402_views.png` combines the hull plan, full game-like
view, front and side. These are exported SCM/DDS mip1 renders with approximate
lighting. Alternate player color uses mip2. The construction icon is independent.

### Solid hull growth from red markup — 24 October 2026

`reference-redline-2026-10-24.png` preserves the user's new annotation. The
hatched regions mean added solid material. The fore-left element is enlarged
with a smooth contour (its top-projected footprint is 28.9% larger than the
previous approved model). The central port rail gains a broad rounded shoulder.
The starboard hull now extends under the right bearing rail, completely filling
the previous channel. The lower starboard spike is integrated into the main
armor outline and shares its closed cap and bevel, rather than floating beside it.

Raised overlapping armor fields, arched structural ribs, island shoulder plates
and low vent ribs add geometric relief. There are no sawtooth edges. Geometry
supplies the added volume; material DDS files, team masks, skeleton, gun pivots,
unit blueprint and script are preserved. Concave armor outlines have rounded
corners, rolled edge geometry and ear-clipped caps. Duplicate tangent records
are averaged within matching position/normal/UV/bone seams before welding,
reducing vertex count while the more detailed geometry increases triangle count.

`redline_shape_checks.json` records the enlarged fore-left projection and 1,615
covered sample points through the new starboard infill. It also checks the
left shoulder and connected projected silhouette of the lower-right spike.
These file/projection checks are not game verification. The previously approved
unit, sources, renders and maps are preserved under
`archive/before-redline-detail-2026-10-24/`. Weapon parameters remain 2×3,000
damage, 0.3-second spacing and range 80. The installed copy is not updated.

## Weapons and inherited parameters

| Property | Value |
| --- | --- |
| Main salvo | **2 × 3,000 damage**, 6,000 total before defenses/misses |
| Firing order / separation | Front, then rear / **0.3 s** (three ticks) |
| Charge | 3 s once for the complete salvo |
| Range / splash | 80 / 4 |
| Weapon rate | Original `RateOfFire = 0.1`, one shared weapon/cooldown |
| AA | Four turrets: each 60 damage, radius 3, 2 shots/s, range 30 |
| Hull / personal shield | 40,000 / 20,000 HP |
| Shield upkeep | 400 energy/s |
| Land / water / reverse speed | 3.6 / 3.6 / 2.5 |
| Mass / energy / build points | 32,000 / 480,000 / 52,000 |

One rack has `MuzzleBones = { 'MainForeMuzzle', 'MainAftMuzzle' }`,
`MuzzleSalvoSize = 2`, `MuzzleSalvoDelay = 0.3`, `ProjectilesPerOnFire = 1`
and damage 3,000 per shell. `RackRecoilDistance = 0` avoids FAF's delayed-salvo
initialization error. There is no second independent main weapon or additional
damage callback. Range, AA, shield, hull, movement and cost retain the original
GGA0401 values from before its 24 October rebalance. GGA0402 keeps its own
40,000 hull HP and 20,000 HP personal shield.

`RackSalvoChargeTime = 3` replaces per-muzzle charging; `MuzzleChargeDelay = 0`.
Otherwise the native firing loop would charge another three seconds for the
second shot, making a 3.3-second gap. Both pods charge together; only the firing
pod's charge visual hides, leaving the rear charged for its shot. Effects reset
on target loss, halt-fire and death. Native weapon timing, interrupted salvos,
cooldown and fire-clock behavior still need match testing.

The tank uses its own `GGP0402` projectile, `GGP0402Charge` visual and
`gga0402_impact_*` emitters. Their original GGA0401 assets and projectile material
maps were copied locally during extraction, preserving their appearance. These
are resources supplied by this mod, not
another mod or an installed-copy dependency. Each projectile receives 3,000
damage from this unit's weapon. Impact visuals add no damage. The clone has
its own geometry, maps, icon, blueprint, script and source generator.

## Regeneration and verification

```powershell
$conceptPython = 'C:\Users\Nestr\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $conceptPython 'mods\seraphim-extra-units\source-assets\GGA0402\generate_concept_tank.py'
```

Requires Python, numpy and Pillow. `--skip-textures` preserves material maps;
`--skip-previews` skips renders/icons; `--previews-only` reads the existing SCM/DDS
and regenerates only renders and icons. `concept_geometry.py` and `supcom_binary.py`
are local project-owned helpers adapted from GGA0401, with no import of the
original model generator. OBJ/MTL, material PNGs and the reference stay in sources.

The mounted local FAF `lua.nx2`, `lua/sim/weapons/DefaultProjectileWeapon.lua`,
confirms the muzzle loop, per-muzzle versus rack charge, delayed salvo and recoil
rules. GGA2401 is the project's working sequential-salvo example; its script and
stock UAL0205 demonstrate rotation slavers with separate hinges. Standard builder
tags and `EXPERIMENTAL MOBILE LAND DIRECTFIRE HOVER` categories preserve the T3
build filters and M28AI land-experimental role. Engine `CanBuild` and actual AI
selection remain unverified.

`export_findings.json` records geometry, skeleton and DDS means; `file_checks.json`
records narrow file/resource checks. `original_unit_hashes.json` records GGA0401
runtime hashes for comparison; the original is unchanged. No test infrastructure
was added. The game was not launched, the installed mod was not updated, and no
local match was run. Aiming, firing, exact shot spacing, interruption, shield,
drift, destruction/wreckage and AI selection need game verification.
