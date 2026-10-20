# Seraphim Rework

This mod is a home for gameplay and balance changes to the Seraphim faction. It currently adds a compact, upgradeable T1 → T2 → T3 mass fabricator line, two Seraphim T3 artillery installations, a T3 point-defense turret, a T1 mobile missile launcher, and an experimental T1 mobile directional shield.

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

`GGA2401` is the T3 Vothuun Salvo Platform, buildable by Seraphim T3 engineers and upgraded commanders. Its model is a tall five-level tower of separate jagged levitating rocks above a five-petal pointed foundation. Each rock is offset to a different side of the centre and carries one broad-breeched, split-blade artillery cannon, following the user's two Seraphim references. Cylindrical barrels, saucer islands and circular plinths have been replaced by angular armor leaves, fractured keels and pointed satellite shards. Materials are aged dark gunmetal with restrained reflective wear on edges and player-colored crop-circle engravings: linked concentric circles, orbital nodes and thin geometric lines. Islands share yaw; each cannon elevates about its own rear hinge via the existing rotation slavers. The footprint remains 4×4. The unit has two SCM LODs, a 1024×1024 material atlas, and an original generated 64×64 construction icon showing its five staggered levels.

The weapon uses the stock Seraphim T2 `XSB2303` artillery class and shell. The baseline was checked against the local FAF 3839 archives and upstream `develop`: T2 range is 115 and shell damage is 2,400. GGA2401 adds exactly 10 to each, for **125 range** and **2,410 damage per shell**. Minimum range 50, splash radius 3, low ballistic arc, normal artillery dispersion and friendly splash damage follow the T2 role; launch speed is 30 to accommodate the extra range.

One shared weapon fires **10 sequential shells**, two from each launcher in order `1,1,2,2,3,3,4,4,5,5`. The interval is 0.2 seconds (two simulation ticks): first-to-last shell takes 1.8 seconds. `RateOfFire = 10/400` gives a nominal 40-second first-shot-to-first-shot cycle, with about 38 seconds between bursts, and `RenderFireClock = true` enables the same native reload bar as T2 artillery. Energy shortages and target acquisition can delay the next volley. No tenfold multiplication of the damage field is used: a complete volley deals 24,100 damage before splash, shields, dispersion and misses, or a nominal 602.5 sustained DPS.

Starting balance: **14,250 HP**, **10,000 mass / 71,500 energy / 8,000 build points**, 28 vision, and **13,000 energy per complete volley**, charged at 650 energy/s. Cost, durability and construction time are five times the stock T2 installation, while the 40-second cycle gives roughly the sustained damage of five T2 guns concentrated into a burst. Balance is provisional. Veteran thresholds are also scaled by five.

The previous weapon failed FAF's initialization rule: nonzero `RackRecoilDistance` cannot be combined with nonzero `MuzzleSalvoDelay`. Recoil is now zero; the stock weapon state machine handles the sequence, energy charge and cooldown. The user confirmed the firing mechanics work well before requesting this floating-island visual rebuild. The weapon blueprint, costs and combat statistics are retained. **The new tower and separate pitch hinges have not been tested in a match**; game verification is left to the user as requested. The existing optional M28AI role hook continues to classify this short-range T3 artillery with tactical/T2 artillery without falsifying its tech or size categories.

Source and regeneration notes: [`source-assets/GGA2401/README.md`](source-assets/GGA2401/README.md).

Adds `GGA2301`, a T3 direct-fire point-defense turret based on the stock Seraphim T2 `XSB2301` Uttaushala. Its Prism Spire model was rebuilt from the 2026-10-20 reference: six plated feet, three curved open frames, a floating double-point player-color crystal, an equatorial ring and a short beam lens. It has two mesh LODs and a 512×512 material atlas with polished silver armor, reflective gunmetal mechanisms, chrome borders and player-color lights/inlays. Paired flowing contours and nested oval markings follow the stock Seraphim material references; high SpecTeam reflection/specular values provide the metallic finish. A one-second activation gently opens the frames; idle slowly rotates and bobs the crystal. Decorative animations do not key the weapon's aiming or muzzle bones. The weapon keeps the stock ultrachromatic beam firing timing and sound cues. It is buildable by T3 Seraphim engineers and commanders, and has upgraded T3 durability and damage: 6,500 HP, 2,000 mass / 17,600 energy / 2,000 build-time cost, 24 vision, 60 range, and 175 beam damage. The rebuilt model still needs local-match visual and tracking confirmation.

## T3 ball-lightning artillery

`GGA2404` is **Vael-Itha**, integrated from the local `seraphim_heavy_turret` revision 9. It is a separate artillery installation alongside `GGA2401` and `GGA2301`, buildable by Seraphim T3 engineers and commanders with T3 engineering. Its levitating ring model, two SCM LODs, textures, animations, icon, projectile mesh and particle effects are included within this mod. The unit and both projectiles have independent IDs and all asset paths point to `seraphim-rework`; the standalone mod is not required.

Original prototype statistics are preserved: **18,000 HP**, **5,000 mass / 50,000 energy / 6,000 build points**, 4×4 skirt, 35 vision, range **25–120**, 2.5-second muzzle charge and `RateOfFire = 0.125`. On land the projectile sinks to the surface and strikes nearby targets every 0.5 seconds for 3 seconds: **400 damage per strike**, radius **5**, up to **2,400 damage per target**. This includes friendly units. Standard phason impacts, including shield interception and water impacts, retain 2,500 damage with radius 5 instead of the ground-lightning sequence. Combat behavior and balance remain provisional; no match was run for this integration.

The optional M28AI hook also classifies `GGA2404` as tactical artillery, preserving its real `TECH3` and `SIZE4` categories. See [integration notes and known limitations](docs/VAEL_ITHA.md).

## T1 mobile missile launcher

Adds the `GGA0101` Seraphim T1 mobile long-range missile launcher, buildable from Seraphim T1–T3 land factories. It reuses the stock Seraphim missile-launcher model, reload animation, projectile, and weapon behavior. The launcher has 45 range, 85 missile damage, 90 mass cost, and 450 build time.

## T1 mobile directional shield

Adds the experimental `GGA0102` Thuum Bulwark, buildable from the Seraphim T1 land factory. It reuses the stock mobile shield generator model and standard shield behavior, with a custom curved forward panel and box collision volume. The panel protects units and objects behind it; its shield has 6,000 health, regenerates at 50 per second after a 3-second delay, and uses 75 energy per second while enabled. Facing, projectile interception, and appearance still need local-match verification.

## Files

- `hook/lua/system/Blueprints.lua` — removes the stock T2 Seraphim fabricator blueprint; the stock T3 remains available.
- `units/GGA1104`, `units/GGA1204`, `units/GGA1304` — new T1, T2, and T3 fabricator blueprints and scripts, with their model assets.
- `units/GGA2301` — T3 Seraphim direct-fire point-defense blueprint, script, Prism Spire meshes, textures, and animations.
- `units/GGA2401` — five-launcher T3 artillery blueprint, script, original meshes and textures.
- `units/GGA2404`, `projectiles/GGP2404`, `projectiles/GGP2404Charge` — Vael-Itha turret, damaging orb and visual charging orb.
- `meshes/ball_lightning`, `effects/emitters/ball_*`, `textures/particles/ball_*` — self-contained ball-lightning visuals.
- `units/GGA0101` — T1 mobile missile launcher blueprint and script.
- `units/GGA0102` — T1 mobile shield blueprint, script, and custom shield mesh.
- `icons/units/GGA*_icon.dds` and `textures/ui/common/icons/units/GGA*_icon.dds` — custom unit icons; `GGA2301` reuses the T2 point-defense icon, while `GGA2401` has an original five-level shard-tower icon with transparent background.
- `source-assets/GGA0102` — source geometry and generator for the custom shield panel.
- `source-assets/GGA2301` — procedural model and animation generator for the Prism Spire turret.
- `source-assets/GGA2401` — independent artillery model generator, editable OBJ, texture sources, exported-SCM previews and archived previous blueprint.

## Installation

Copy the entire `seraphim-rework` folder into the FAF data `mods` directory and enable **Seraphim Rework**.

## M28AI compatibility

The original seven active unit blueprints were audited against the locally installed M28AI
v327; the eighth, `GGA2404`, has also had its builder categories and artillery filters checked against those sources. The T1 missile launcher now has the standard `SILO` role, and the T1 mobile
shield is available from T1–T3 land factories. The existing fabricator and T3 point
defense categories already match M28AI's economic and defensive filters.

An optional hook in this mod classifies `GGA2401` and `GGA2404` as tactical artillery for M28AI,
including its firebase/threat filters, while preserving its real T3 technology and
size. M28AI's own files are not modified and it is not a required dependency.
The stock AI's decisions about when to build units remain relevant: in particular,
its normal fabricator construction task targets T3, and mobile shield production
starts with T2 factories. No early T1/T2 fabricator strategy was added.

See [the complete role audit and limitations](docs/M28AI_COMPATIBILITY.md).
Source/category checks do not confirm actual M28AI behavior in a local match.
