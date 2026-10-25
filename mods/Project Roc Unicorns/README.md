# Project Roc Unicorns

This mod is a home for gameplay and balance changes to the Seraphim faction. It currently adds a compact, upgradeable T1 → T2 → T3 mass fabricator line, a T4 shielded power generator, one experimental hover assault tank, two Seraphim T3 artillery installations, a T3 point-defense turret, a T1 mobile missile launcher, and a prototype T2 mobile directional shield.

`GGA0402` Itha-Suun and `GGA0403` Itha-Vael are included in the independent
[Seraphim Additional Units](../seraphim-extra-units/README.md) mod on 25 October 2026.
These two tanks are no longer included here. GGA2404 Vael-Itha remains in
Project Roc Unicorns. Both mods can be enabled together.

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

Current durability is **8,000 hull HP** plus a **32,000 HP personal shield**.
The native `PersonalShield` mechanism routes damage only for the owner and has
no surrounding projectile-interception dome; the hull stays metallic and native
Seraphim shield-hit effects show impacts. The shield regenerates
**1,000 HP/s after 5 seconds**, and takes **20 seconds** to recharge after
collapse, or **5 seconds** after an energy outage. Its configured shield size
is **7**. Initial build cost:
**32,000 mass / 480,000 energy / 52,000 build points**. Balance is provisional.

SCM/DDS files and rendered previews were checked. Loading, building, movement,
aiming, shield behavior and firing still need verification in a local match;
the game was not launched for this addition. M28AI's land-experimental category
matches this unit; actual AI selection and engine `CanBuild` are unverified.
See [sources, previews and verification notes](source-assets/GGA0401/README.md).

## T4 experimental power generator

`GGA1401` **Uya-Iava** produces **25,000 energy/s** and carries a **26,000 HP shield dome, size 12**, with no energy upkeep. Its hull has **24,000 HP**. It costs **6,000 mass / 90,000 energy / 11,000 build points**. It uses exactly the stock Seraphim T3 generator's **8×8 construction skirt**, **5×5 footprint** and skirt offsets. Build it with Seraphim T3 engineers or commanders with T3 engineering. Its original rounded metallic model has an open energy throat, five tall petals, eleven lower petals, six root pods and three orbiting Seraphim shards. Two fragments travel clockwise and one counterclockwise, viewed from above, with a 32-second orbital period. Player-color inlays, two SCM LODs, core rotation, vertical drift and a custom construction icon are included.

The 2026-10-21 visual revisions replace the wide platter with a compact foundation and five tall, rounded swept petals like the stock T3 generator, then add two tiers of lower leaves and replace the floating calderas with closed, curved metallic shards. The 2026-10-22 addition places two more irregular islands above the crown: a central island spins clockwise in place once per 16 seconds, while a smaller satellite circles it counterclockwise once per 32 seconds, viewed from above. The original three orbiting shards remain. Visuals retain the stock XSB1301 ground-circle tarmac and `ST3PowerAmbient` rising light/ring/distortion effects, referenced directly from the game. Prior models are archived in the unit's source directory. Particle effects and orbital animation still require in-game verification.

The shield regenerates **1,000 HP/s after 3 seconds** and takes **10 seconds** to recharge after collapse or **5 seconds** after energy depletion. Power remains active when the shield is toggled off. The reactor retains standard T3 power adjacency. Destruction of a completed reactor releases the stock **Othuy residual-energy storm**, using Ythotha's spawn method and effects. Ordinary explosion visuals, blast damage, flying debris and explosion sounds are disabled; reclaimable wreckage remains. Unfinished construction and normal reclaim do not spawn a storm. It is a separate experimental build, not a T3 upgrade. [Model, balance, source checks and limitations](source-assets/GGA1401/README.md).

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

`GGA2404` **Vael-Itha** is back in Project Roc Unicorns. This stationary T3
ball-lightning artillery is buildable by Seraphim T3 engineers and commanders
with T3 engineering. Its model, textures, icons, projectiles, army-colored
particle effects and authoring sources are all supplied here. The correction
only restores ownership and asset paths; its combat values, procedural charge,
aiming and firing logic are unchanged. Additional Units is not required.

The optional M28AI hook classifies both GGA2401 and GGA2404 as tactical artillery,
while retaining their real TECH3 categories. [Vael-Itha source and current
parameters](source-assets/GGA2404/README.md) · [History](docs/VAEL_ITHA.md).
The relocation has been checked from files; no new match was run.

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
- `units/GGA2404`, `projectiles/GGP2404`, `projectiles/GGP2404Charge` — Vael-Itha artillery and its projectiles.
- `effects/emitters/ball_*`, `textures/particles/ball_army_ramp.dds`, `lua/vael_itha_effects.lua` — Vael-Itha army-color lightning effects.
- `units/GGA0101` — T1 mobile missile launcher blueprint, script, original meshes, textures and reload animation.
- `props/GGA0101_wreck` — explicit reclaimable Thuunar wreck prop, damaged meshes and scorched texture.
- `units/GGA0102` — T2 mobile shield blueprint, script, and custom shield mesh.
- `icons/units/GGA*_icon.dds` and `textures/ui/common/icons/units/GGA*_icon.dds` — custom unit icons; `GGA2301` has its own transparent Ishal-Thar turret icon, while `GGA2401` has an original five-level shard-tower icon with transparent background.
- `source-assets/GGA0101` — independent Thuunar model generator, editable OBJ, material sources, SCM previews and previous configuration archive.
- `source-assets/GGA0102` — source geometry and generator for the custom shield panel.
- `source-assets/GGA2301` — procedural model and animation generator for the Prism Spire turret.
- `source-assets/GGA2401` — independent artillery model generator, editable OBJ, texture sources, exported-SCM previews and archived previous blueprint.

## Installation

### Ishal-Thar — 25 October 2026

`GGA2301` is now named **Ishal-Thar** in game. Its repainted dark silver/gunmetal
atlas and native Seraphim shader replace the former pale Unit material; the
player-color contours, nested oval markings, crystal and metallic shine remain.
It has an original transparent build-menu icon in both FAF paths. Meshes,
animations and combat values are unchanged. DDS mipmaps and SCM previews were
checked; in-game appearance awaits a local match. Only the project working copy
was updated. [Sources and previous-version backup](source-assets/GGA2301/README.md).

### Material adjustment — 22 October 2026

The custom unit hulls received darker materials to sit closer to stock
Seraphim buildings: reduced albedo brightness and reflection, with metallic
gloss and player-color details retained. GGA1104/GGA1204/GGA1304 receive original
steel/gunmetal Seraphim textures, fine concentric inlays and the native Seraphim
shader, keeping their meshes and animations. GGA2301's packed normal channels
and independent material mipmaps are also corrected. The reused stock GGA0102
hull is unchanged. [Sources, original-material backup and DDS/SCM comparisons](source-assets/material-adjustment-2026-10-22/README.md).
File checks and rendered previews were performed; in-game appearance still
needs confirmation in a new local match.

Copy the entire `Project Roc Unicorns` folder into the FAF data `mods` directory and enable **Project Roc Unicorns**.

## M28AI compatibility

The original role audit used the locally installed M28AI v327. The T1 missile launcher now has the standard `SILO` role, and the T2 mobile
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
