# Seraphim Rework

This mod is a home for gameplay and balance changes to the Seraphim faction. It currently adds a compact, upgradeable T1 → T2 → T3 mass fabricator line, a T4 shielded power generator, an experimental hover assault tank, two Seraphim T3 artillery installations, a T3 point-defense turret, a T1 mobile missile launcher, and a prototype T2 mobile directional shield.

## Experimental hover assault tank

`GGA0401` **Itha-Yen** is a separate Seraphim experimental hover tank, built by T3
engineers and commanders with T3 engineering. Its original rounded steel model
occupies approximately **4×6** game units and includes four independent AA
turrets, an open focusing cannon, two mesh LODs, native Seraphim materials,
player-color inlays and a custom construction icon.

The naval-style hull rebuild follows the user's Seraphim ship reference: a swept
central keel, one long port island, two separate starboard islands, an offset
aft shard and three unequal open fins. Hull sections have real open gaps and
gently drift at different phases; AA mounts are parented to their moving islands.
The exported model measures **3.96×5.90** horizontally. The existing reflective
metal and player-color patterns are retained. Updated meshes, sources, previews
and construction icon are included; the new model/drift still need match testing.

The main gun fires a large phason sphere along a **direct-fire trajectory** at
**80 range**, with **6,000 damage**, **4 splash radius**, **3 seconds of visible
charging**, and `RateOfFire = 0.1`. The four AA turrets each deal **60 damage**,
with **3 splash radius**, **2 shots/s**, and **30 range**, targeting aircraft
independently. The tank moves at **3.6** on both land and water, compared with
the stock Ythotha's **2.5**; reverse speed is **2.5**.

The 22 October balance revision halves main-shell damage and reduces range from
100 to 80. Impacts add a brief bright white flash, an expanding blue energy ring
and outward electrical arcs; these are visual particles with no extra damage.
The same flash/ring/arcs play on shield hits. Their appearance needs match verification.

Starting durability is **40,000 hull HP** plus a **20,000 HP personal shield**.
The native `PersonalShield` mechanism routes damage only for the owner and has
no surrounding projectile-interception dome; the hull stays metallic and native
Seraphim shield-hit effects show impacts. The shield uses **400 energy/s**,
regenerates **200 HP/s after 5 seconds**, and takes **30 seconds** to recharge
after collapse, or **5 seconds** after an energy outage. Initial build cost:
**32,000 mass / 480,000 energy / 52,000 build points**. Balance is provisional.

SCM/DDS files and rendered previews were checked. Loading, building, movement,
aiming, shield behavior and firing still need verification in a local match;
the game was not launched for this addition. M28AI's land-experimental category
matches this unit; actual AI selection and engine `CanBuild` are unverified.
See [sources, previews and verification notes](source-assets/GGA0401/README.md).

## T4 experimental power generator

`GGA1401` **Uya-Iava** produces **15,000 energy/s** and carries a compact **6,000 HP shield dome, diameter 18**, with no energy upkeep. It uses exactly the stock Seraphim T3 generator's **8×8 construction skirt**, **5×5 footprint** and skirt offsets. Build it with Seraphim T3 engineers or commanders with T3 engineering. Its original rounded metallic model has an open energy throat, five tall petals, eleven lower petals, six root pods and three orbiting Seraphim shards. Two fragments travel clockwise and one counterclockwise, viewed from above, with a 32-second orbital period. Player-color inlays, two SCM LODs, core rotation, vertical drift and a custom construction icon are included.

The 2026-10-21 visual revisions replace the wide platter with a compact foundation and five tall, rounded swept petals like the stock T3 generator, then add two tiers of lower leaves and replace the floating calderas with closed, curved metallic shards. The 2026-10-22 addition places two more irregular islands above the crown: a central island spins clockwise in place once per 16 seconds, while a smaller satellite circles it counterclockwise once per 32 seconds, viewed from above. The original three orbiting shards remain. Visuals retain the stock XSB1301 ground-circle tarmac and `ST3PowerAmbient` rising light/ring/distortion effects, referenced directly from the game. Prior models are archived in the unit's source directory. Particle effects and orbital animation still require in-game verification.

Initial balance: **24,000 hull HP**, **20,000 mass / 360,000 energy / 30,000 build points**; shield regeneration **100 HP/s after 3 seconds**, collapse recharge **25 seconds**. Power remains active when the shield is toggled off. The reactor retains standard T3 power adjacency. Destruction of a completed reactor releases the stock **Othuy residual-energy storm**, using Ythotha's spawn method and effects. Ordinary explosion visuals, blast damage, flying debris and explosion sounds are disabled; reclaimable wreckage remains. Unfinished construction and normal reclaim do not spawn a storm. It is a separate experimental build, not a T3 upgrade. [Model, balance, source checks and limitations](source-assets/GGA1401/README.md).

Optional M28AI v327 hooks recognize the reactor as power and allow replacing a normal Seraphim T3 generator choice when income reaches **80 mass/s and 10,000 energy/s**, stored mass is at least **5,000**, energy storage is at least **50%**, and no reactor exists. The original builder/restriction checks remain active; choices have a 60-second cooldown. Cheapest-only requests retain the ordinary generator. No false TECH3 or mass-production categories were added. File checks and exported-SCM previews do not confirm game behavior or actual AI selection. This unit has not yet been tested in a local match.

## Mass fabricator line

Each tier uses its corresponding model set originally from `seraphim_t1_fabricator`: T1 uses `zsb1106`, T2 uses `zsb1206`, and T3 uses `zsb1306`. Their two LODs, textures, and active work animations are stored inside this mod under each unit's folder. Placement uses the native 2×2 skirt and its `-0.5` offsets, without an explicit `Footprint` field. Each tier applies the same adjacency bonus table and mass production rate as a mass extractor of that tier. The mod uses a conversion rate of 150 energy per 1 mass produced, instead of the standard 200: at full output, T1 uses 300 energy/s, T2 uses 900 energy/s, and T3 uses 2,700 energy/s.

The T1 fabricator is buildable by Seraphim engineers at T1–T3 and by commanders only after they reach T2, following the Hydrocarbon Power Plant builder categories. T1 and T2 have `BuildRate = 10`, matching the Hydrocarbon upgrade example, so they can perform their own next-tier upgrades; T3 is the final tier.

Costs are twice the matching Seraphim mass extractor's `BuildCostMass`, `BuildCostEnergy`, and `BuildTime` (build points). Energy upkeep follows the 150-energy-per-mass rate at each tier's full mass production:

| Tier | Mass | Energy | Build points | Mass production | Energy consumption |
| --- | ---: | ---: | ---: | ---: | ---: |
| T1 | 72 | 720 | 120 | 2/s | 300/s |
| T2 | 1,800 | 10,800 | 1,800 | 6/s | 900/s |
| T3 | 9,200 | 63,250 | 5,750 | 18/s | 2,700/s |

The stock Seraphim T2 fabricator blueprint `XSB1104` is removed from the active unit blueprint table. The stock T3 fabricator `XSB1303` remains available alongside the mod's custom T3 fabricator.

## T3 rapid artillery

`GGA2401` is the T3 Vothuun Salvo Platform, buildable by Seraphim T3 engineers and upgraded commanders. It is a tall five-level tower of separate levitating islands above a five-petal foundation; each offset island carries one broad-breeched, split-leaf artillery cannon. The 2026-10-21 rebuild follows the user's corrected Seraphim style and inspection of stock XSB2301/XSB2303/XSB2401: continuous rounded surfaces, rolled armor edges and slightly brighter reflective steel replace the angular cut-metal look. Approved crop-circle engravings are preserved pixel for pixel. Materials now use the stock `Seraphim` shader with player color in Albedo.A and packed G/A normals, following `effects/mesh.fx`. Islands share yaw; each cannon elevates about its own rear hinge via the existing rotation slavers. The footprint remains 4×4. The unit has two SCM LODs, a 1024×1024 material atlas, and its unique 64×64 construction icon. [Stock-model findings](source-assets/GGA2401/stock-seraphim-study.md).

The weapon uses the stock Seraphim T2 `XSB2303` artillery class and shell. The baseline was checked against the local FAF 3839 archives and upstream `develop`: T2 range is 115 and shell damage is 2,400. GGA2401 adds exactly 10 to each, for **125 range** and **2,410 damage per shell**. Minimum range 50, splash radius 3, low ballistic arc, normal artillery dispersion and friendly splash damage follow the T2 role; launch speed is 30 to accommodate the extra range.

One shared weapon fires **10 sequential shells**, two from each launcher in order `1,1,2,2,3,3,4,4,5,5`. The interval is 0.2 seconds (two simulation ticks): first-to-last shell takes 1.8 seconds. `RateOfFire = 10/400` gives a nominal 40-second first-shot-to-first-shot cycle, with about 38 seconds between bursts, and `RenderFireClock = true` enables the same native reload bar as T2 artillery. Energy shortages and target acquisition can delay the next volley. No tenfold multiplication of the damage field is used: a complete volley deals 24,100 damage before splash, shields, dispersion and misses, or a nominal 602.5 sustained DPS.

Starting balance: **14,250 HP**, **10,000 mass / 71,500 energy / 8,000 build points**, 28 vision, and **13,000 energy per complete volley**, charged at 650 energy/s. Cost, durability and construction time are five times the stock T2 installation, while the 40-second cycle gives roughly the sustained damage of five T2 guns concentrated into a burst. Balance is provisional. Veteran thresholds are also scaled by five.

The previous weapon failed FAF's initialization rule: nonzero `RackRecoilDistance` cannot be combined with nonzero `MuzzleSalvoDelay`. Recoil is now zero; the stock weapon state machine handles the sequence, energy charge and cooldown. The user confirmed the firing mechanics work well before requesting this floating-island visual rebuild. The weapon blueprint, costs and combat statistics are retained. **The new tower and separate pitch hinges have not been tested in a match**; game verification is left to the user as requested. The existing optional M28AI role hook continues to classify this short-range T3 artillery with tactical/T2 artillery without falsifying its tech or size categories.

Source and regeneration notes: [`source-assets/GGA2401/README.md`](source-assets/GGA2401/README.md).

The 2026-10-21 black-body rendering defect was traced to DDS mip export: ordinary
RGBA downsampling treated material masks as transparency and erased reflection
data below mip0. Material channels now downsample independently; all eleven mip
levels retain their data. Geometry, firing behavior and line-mask pixels are
unchanged. The game-view preview now samples an exported DDS mip rather than PNGs.

Adds `GGA2301`, a T3 direct-fire point-defense turret based on the stock Seraphim T2 `XSB2301` Uttaushala. Its Prism Spire model was rebuilt from the 2026-10-20 reference: six plated feet, three curved open frames, a floating double-point player-color crystal, an equatorial ring and a short beam lens. It has two mesh LODs and a 512×512 material atlas with polished silver armor, reflective gunmetal mechanisms, chrome borders and player-color lights/inlays. Paired flowing contours and nested oval markings follow the stock Seraphim material references; high SpecTeam reflection/specular values provide the metallic finish. A one-second activation gently opens the frames; idle slowly rotates and bobs the crystal. Decorative animations do not key the weapon's aiming or muzzle bones. The weapon keeps the stock ultrachromatic beam firing timing and sound cues. It is buildable by T3 Seraphim engineers and commanders, and has upgraded T3 durability and damage: 6,500 HP, 2,000 mass / 17,600 energy / 2,000 build-time cost, 24 vision, 60 range, and 175 beam damage. The rebuilt model still needs local-match visual and tracking confirmation.

## T3 ball-lightning artillery

`GGA2404` is **Vael-Itha**, originally integrated from the local `seraphim_heavy_turret` revision 9 and subsequently corrected after user match feedback. It is a separate artillery installation alongside `GGA2401` and `GGA2301`, buildable by Seraphim T3 engineers and commanders with T3 engineering. Its levitating ring model, two SCM LODs, textures, procedural animations, icon and particle effects are included within this mod. The unit and both projectiles have independent IDs and all mod asset paths point to `seraphim-rework`; the standalone mod is not required.

The 2026-10-20 correction darkens the reflective metal moderately and replaces
angular markings with linked crop-circle inlays. Every colored model surface uses
the player's army mask. Charge and projectile release now share the center of the
two rings, with no late forward movement. The smooth visible sphere is replaced by
six Othuy-style electrical particle layers, based on the XSL0402 residual energy
entity spawned after Ythotha dies. Both charge and flight use the same player-color
effect, with standard FAF textures referenced in place. Runtime animation remains
procedural; the inactive full-rig SCA clips and retired sphere/violet assets are
archived. The new generator, editable Blender file and exported-SCM views are in
[`source-assets/GGA2404`](source-assets/GGA2404/README.md). Structural and mocked Lua
checks passed; this correction still needs a match check for rendering and FX.

The October 21 refinement restores inward-facing gondola/ring illumination,
moves both gondolas inward so ring-center separation is 15% smaller, and widens
markings by 50%. Flat surface inlays with a concave normal map replace raised
pattern wires. This gives an engraved appearance without Boolean grooves and
reduces the mesh cost. Centered charge and shot, army colors and damage remain
as described above. This refinement has not been checked in a match.

The subsequent straight-gondola revision removes the inward-curving tips while
preserving all three DDS maps byte for byte. A successful shot triggers a 0.1 s
delay, 0.3 s closing, and 7.6 s of automatic charge growth/reopening. The full orb
is held ready without a target. The old target-dependent muzzle charge is removed;
the native firing state is gated on the independent ready flag. The closed gap is
about 0.0985 game units and the common central release point is unchanged.

The high-arc mortar revision uses **18,000 HP**, **6,500 mass / 65,000 energy / 7,800 build points**, a 4×4 skirt, 35 vision and range **35–150**. Native high-arc ballistics and speed 32 give an estimated 67–85 degree elevation and 12–13 second flight on flat ground. The floating assembly is raised 0.20 game units; conservative foundation clearance exceeds 0.28 in both LODs at any pitch, including hover/recoil. `FiringRandomness = 0.24` targets approximately radius-3 spread at range 150, tightening at shorter distances. These estimates need a match check.

`RateOfFire = 0.125` gives an eight-second nominal post-shot cycle. Each autonomous charge costs **2,000 energy**; native economy-event progress drives both growth and gondola opening. Energy shortages delay readiness, and holding a ready orb drains nothing. On land the projectile sinks to the surface and strikes nearby targets every 0.5 seconds for 3 seconds: **400 damage per strike**, radius **5**, up to **2,400 damage per target**, including friendly units. There is no additional dry-land impact damage. Shield/water impacts instead use a 2,400-damage phason impact with radius 5. Combat behavior and balance remain provisional; this revision has not been run in a match.

The October 22 follow-up uses native Seraphim shading, packed G/A normals and
stock-dark building metal (main albedo median about 16/255, retaining reflections).
Rotator setters no longer depend on fluent returns: strict nil-return API checks
now complete initial charging, firing and recharging. Four one-time game-log stage
markers were added for diagnosis. The original match's game.log is unavailable;
this follow-up still needs a match check for the reported firing failure.

The optional M28AI hook also classifies `GGA2404` as tactical artillery, preserving its real `TECH3` and `SIZE4` categories. See [integration notes and known limitations](docs/VAEL_ITHA.md).

## T1 mobile missile launcher

Adds the `GGA0101` **Thuunar** Seraphim T1 mobile long-range missile launcher, buildable from Seraphim T1–T3 land factories. The 2026-10-21 visual rebuild replaces the borrowed T2 `XSL0111` mesh and reload clip with an original compact two-track carrier and a newly modeled open, inclined twin-leaf launch cradle inspired by the same launcher. Its lower, simpler chassis omits the T2 unit's broad three-prong hull and tall rear fins. Rounded silver-steel armor carries thin player-color lines and crop-circle engravings, using the native `Seraphim` material channels. Two SCM LODs, three 512×512 material maps, a skeleton-compatible reload animation and a new transparent build icon are included.

Destroyed Thuunars use an explicit reclaimable prop with their own damaged SCM LODs, collapsed chassis, broken launch rail and scorched texture. `Wreckage.UseCustomMesh = true` tells FAF to retain this prop's mesh instead of substituting an automatically generated unit wreck mesh. Reclaim multipliers remain unchanged. The script uses the standard `SLandUnit` and `SLaanseMissileWeapon`; the stock projectile, firing cycle, 350 hull HP, 45 range, 85 missile damage, 90 mass / 800 energy and 450 build points are preserved.

The model, DDS mipmaps, bone bindings, reload clip and custom wreck path were checked from files, with previews rendered from the exported SCM and DDS. Loading, firing, track appearance, destruction and reclaim have **not** been tested in a match. [Model sources, regeneration and verification notes](source-assets/GGA0101/README.md).

## T2 mobile directional shield

Adds the prototype `GGA0102` Thuum Bulwark, now a **T2** unit buildable from Seraphim T2–T3 land factories, with the T2 strategic shield icon. Its existing blueprint ID is retained. It reuses the stock mobile shield generator model and standard shield behavior, with a custom curved forward panel and box collision volume intended to protect units behind it.

Starting balance: **250 hull HP**, **5,000 shield HP**, **300 mass / 2,400 energy / 1,200 build points**, **90 energy/s** while enabled, **60 shield HP/s** regeneration after a **3-second** damage-free delay, **30-second** recharge after shield depletion, and **5-second** recharge after energy depletion. Forward/reverse speed is **3.5**, vision is **20**, and transport class remains **2**. Panel geometry and collision dimensions are unchanged.

The baseline was checked against the local FAF `units.nx5` and upstream [UEF Parashield](https://github.com/FAForever/fa/blob/develop/units/UEL0307/UEL0307_unit.bp), [Aeon Asylum](https://github.com/FAForever/fa/blob/develop/units/UAL0307/UAL0307_unit.bp), and [Seraphim Athanah](https://github.com/FAForever/fa/blob/develop/units/XSL0307/XSL0307_unit.bp). The stock T2 shields have 3,000–3,500 shield HP and cost 220 mass; Athanah is T3 with 10,000 shield HP at 720 mass. Thuum trades all-around coverage for a stronger forward panel, at a higher cost and energy upkeep than either stock T2 shield. Its weak hull remains vulnerable from the flanks and rear. Balance is provisional; facing, projectile interception, appearance and actual M28AI use still need local-match verification. No match was run for this conversion.

## Files

- `hook/lua/system/Blueprints.lua` — removes the stock T2 Seraphim fabricator blueprint; the stock T3 remains available.
- `units/GGA1104`, `units/GGA1204`, `units/GGA1304` — new T1, T2, and T3 fabricator blueprints and scripts, with their model assets.
- `units/GGA2301` — T3 Seraphim direct-fire point-defense blueprint, script, Prism Spire meshes, textures, and animations.
- `units/GGA2401` — five-launcher T3 artillery blueprint, script, original meshes and textures.
- `units/GGA2404`, `projectiles/GGP2404`, `projectiles/GGP2404Charge` — Vael-Itha turret, damaging orb and visual charging orb.
- `effects/emitters/ball_*`, `textures/particles/ball_army_ramp.dds`, `lua/vael_itha_effects.lua` — Othuy-style ball-lightning visuals, using standard FAF texture references and a custom army-color ramp.
- `units/GGA0101` — T1 mobile missile launcher blueprint, script, original meshes, textures and reload animation.
- `props/GGA0101_wreck` — explicit reclaimable Thuunar wreck prop, damaged meshes and scorched texture.
- `units/GGA0102` — T2 mobile shield blueprint, script, and custom shield mesh.
- `icons/units/GGA*_icon.dds` and `textures/ui/common/icons/units/GGA*_icon.dds` — custom unit icons; `GGA2301` reuses the T2 point-defense icon, while `GGA2401` has an original five-level shard-tower icon with transparent background.
- `source-assets/GGA0101` — independent Thuunar model generator, editable OBJ, material sources, SCM previews and previous configuration archive.
- `source-assets/GGA0102` — source geometry and generator for the custom shield panel.
- `source-assets/GGA2301` — procedural model and animation generator for the Prism Spire turret.
- `source-assets/GGA2401` — independent artillery model generator, editable OBJ, texture sources, exported-SCM previews and archived previous blueprint.

## Installation

### Material adjustment — 22 October 2026

All eight custom unit hulls now use darker materials to sit closer to stock
Seraphim buildings: reduced albedo brightness and reflection, with metallic
gloss and player-color details retained. GGA1104/GGA1204/GGA1304 receive original
steel/gunmetal Seraphim textures, fine concentric inlays and the native Seraphim
shader, keeping their meshes and animations. GGA2301's packed normal channels
and independent material mipmaps are also corrected. The reused stock GGA0102
hull is unchanged. [Sources, original-material backup and DDS/SCM comparisons](source-assets/material-adjustment-2026-10-22/README.md).
File checks and rendered previews were performed; in-game appearance still
needs confirmation in a new local match.

Copy the entire `seraphim-rework` folder into the FAF data `mods` directory and enable **Seraphim Rework**.

## M28AI compatibility

The original seven active unit blueprints were audited against the locally installed M28AI
v327; the eighth, `GGA2404`, has also had its builder categories and artillery filters checked against those sources. The T1 missile launcher now has the standard `SILO` role, and the T2 mobile
shield is available from T2–T3 land factories. The existing fabricator and T3 point
defense categories already match M28AI's economic and defensive filters.

An optional hook in this mod classifies `GGA2401` and `GGA2404` as tactical artillery for M28AI,
including its firebase/threat filters, while preserving its real T3 technology and
size. M28AI's own files are not modified and it is not a required dependency.
The stock AI's decisions about when to build units remain relevant: in particular,
its normal fabricator construction task targets T3, and mobile shield production
starts with T2 factories. No early T1/T2 fabricator strategy was added.

See [the complete role audit and limitations](docs/M28AI_COMPATIBILITY.md).
Source/category checks do not confirm actual M28AI behavior in a local match.
