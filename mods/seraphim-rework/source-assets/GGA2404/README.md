# GGA2404 — Vael-Itha, revision 2026-10-22

The original twin-gondola silhouette, floating foundation and empty coaxial rings
are retained. The current steel albedo follows dark stock building values; SpecTeam R/G retain
environment reflection and sunlight highlights. Old lozenges and zigzag decoration
are replaced with linked concentric ellipses, satellite circles and paired orbital
tracks on the petals, gondolas and ring faces. All colored atlas tiles have a full
army mask; metallic tiles remain neutral. The root bone is named `GGA2404`.

The October 21 revision restores the inward-facing luminous gondola panels by
correcting their face winding, and also corrects the right ring lining's facing.
Both whole gondolas move 0.12 game units toward the center: ring-axis separation
is 1.60 → 1.36 (15 percent). Shell dimensions, ring bores and the centered shot
remain unchanged. Gondola bone origins follow the translated meshes.

All 170 pattern tubes are replaced with surface-projected flat inlays, 1.5 times
their former stroke width. A concave tangent-space normal profile gives shallow
engraved shading. This is a normal-map recess, not a Boolean cut into the metal;
the inlay surface sits 0.0015 units above the receiving skin to avoid z-fighting.
Closed foundation petals and the mirrored left metal ring have outward winding
corrected before projection. The new LODs have 35,454 / 14,210 triangles, compared
with 65,558 / 25,573 in the previous version. `engraved_inlays.py` performs this
projection during regeneration. The prior October 20 revision is preserved in
`archive/before-2026-10-21-inlay-correction.zip`.

## Straight hulls and autonomous recharge

The subsequent October 21 revision holds `hull_values(t).top` at its middle
value, 1.79875, along the entire hull. This removes the inward hooks created by
the former end rise after the 90-degree roll. UV layout, ornamental paths and
all three runtime DDS maps are preserved; the maps were compared byte for byte.
Ring axes, the central shot origin and the fully open 1.36 spacing are retained.

Two native sliders move the complete GondolaL/GondolaR branches 0.42 inward each
when closed. The closest details still have 0.0985 game units of clearance, with
no resizing of the shell or bore. The sliders follow the same yaw/pitch/recoil
parents as the rings. Initial construction starts in the closed pose and begins
charging even without a target. Recharge is an independent unit thread.

After a successfully created projectile, the charge is consumed, the gun holds
open for one simulation tick (0.1 s), and closes over three ticks (0.3 s).
The next orb then grows while the gondolas reopen over 76 ticks (7.6 s).
At `RateOfFire = 0.125`, the nominal post-shot cycle is eight seconds.
The period is sampled from the live weapon rate when a shot succeeds. A complete
charge stays fully open and visible until fired, including while there is no
target or a hold-fire order. Target loss does not cancel the unit recharge.

`MuzzleChargeDelay` is zero: the old target-dependent 2.5-second wait is replaced,
not added to the autonomous cycle. A narrow RackSalvoFiringState gate waits for
`ChargeReady` and checks target/hold-fire before calling the native firing state.
Only a successful native CreateProjectileAtMuzzle starts the next cycle; failure
does not consume the ready orb. Death invalidates the unit thread and clears FX.
The existing full-width mesh field is hidden during closing/partial opening so
it cannot intersect the almost closed gun; the scaled particle charge supplies
electricity during growth. The mesh field returns when fully open.

The preceding accepted version, including its unit script and model sources, is
preserved in `archive/before-2026-10-21-auto-recharge.zip`. Native weapon hook
signatures/state behavior were checked against installed FAF
`lua/sim/weapons/DefaultProjectileWeapon.lua`. Independent charge, ready hold,
failure/success, cancellation and death were checked with mocked APIs outside the
repo. The animation is not yet verified in a FAF match.

## Rebuild

Run `generate_materials.py` with Python, numpy and Pillow, then run Blender 4.5:

```text
python generate_materials.py
blender -b --python generate_turret.py
python preview_scm.py
```

Run from any directory, supplying the paths to these scripts. The scripts find the
mod relative to their own location. They overwrite only this turret's material and
mesh files and its `ball_*` effects. No other mod or installed game directory is
required to generate the model. The baseline PNGs are author-owned source maps.
The stock particle textures are runtime references, not copied game resources.

`generate_turret.py`, `rich_base.py`, `ring_gondolas.py`, and `native_export.py`
adapt the authoring generators from the original standalone turret. Blender is
used directly, without a third-party export addon. SCM sections are aligned to
32 bytes. `GGA2404_source.blend` preserves named objects and rigid bone groups.
`preview_scm.py` adapts this mod's GGA2301 software renderer and reads the exported
SCM. Front, side, overhead and alternate-player-color PNGs approximate lighting;
they are not game screenshots. Charge effects are not drawn by that mesh renderer.

## Centered shot and animation

The Charge, Muzzle and Recoil origins coincide at native coordinates
`(0,58,3.2)`, or `(0,2.9,0.16)` after `UniformScale=0.05`. The ring axis passes
through that point. The existing blueprint references `Muzzle`, so both aim and
projectile creation use the new central position in either LOD. There is no
ChargeSlider or late movement toward the front of the gun. Aim and hover affect
both points through their common parents. Charge rotation has zero local offset.

Runtime hover, field rotation, charge growth and angular recoil remain procedural
Lua animations. Obsolete full-rig SCA clips are archived and removed from runtime;
they keyed aiming bones and are not suitable as decorative animations. No animator
overrides weapon aiming. The saved Blender model is the bind pose.

## Othuy-style orb

The reference is **XSL0402 Othuy**, spawned by XSL0401 Ythotha's death script.
Othuy hides its body and uses `OthuyAmbientEmanation` layers rather than a visible
solid ball. This revision follows that construction using the same native
`electricity_08`, `electricity_09`, `glow_02` and `electricity_beam_02` textures,
with new small-scale emitter configurations and a player-color ramp.
It does not spawn a full experimental unit or inherit its movement/weapon damage.

Both projectile blueprints explicitly use the stock `/meshes/game/nil_mesh`.
The visible orb consists of six particle layers: short arcs, surface flashes,
a soft luminous core, haze, motes and inner electrical flicker. The charging orb
uses the same layers, scaled as charge grows; cancellation destroys its emitters.
The live orb pulses and retains the previous trajectory and ground-hazard logic.

`lua/vael_itha_effects.lua` selects one of the 19 standard FAF lobby army colors
from `ScenarioInfo.ArmySetup`. It sets the verified `RAMPSELECTION_CURVE` emitter
parameter; targeted beams use `SetBeamParam` with STARTCOLOR/ENDCOLOR RGB.
The ramp is 64×256 RGBA without mipmaps, with guarded color bands. Colored sprites
from the old fixed-violet prototype are no longer runtime resources. A custom
palette mod needs the ramp regenerated to match its palette. UI-only recoloring or
late scripted army-color changes are not tracked by this lobby-based FX lookup.

Ground strikes still last 3 seconds, radius 5, six strikes of 400, including own and
allied land units. No target means no long targeted beam. Shield/water fallback
uses 2400 native phason damage and replaces its fixed-color impact particles.
External shield ray interception for direct ground damage remains a prototype
limitation; the change does not introduce a new damage system.

## High-arc mortar balance, October 21

Range is 35–150, matching the UEF T3 battleship's main-gun maximum. Cost is 6500
mass / 65000 energy / 7800 build points; health remains 18000. The muzzle and
projectile speeds both equal 32, with native gravity and RULEUBA_HighArc. An
analytical flat-ground estimate gives elevation 67.3–85.2 degrees and flight
12.1–13.1 seconds; the earlier conversational 5–7 second estimate was incorrect
for this steep arc with stock gravity. These are calculations, not match results.

FiringRandomness=0.24 uses the installed DefaultProjectileWeapon empirical
relationship (12 * spread radius / distance): approximately radius 3 at range
150, 2 at 100, 1.5 at 75 and 0.7 at 35. Actual dispersion must be measured in FAF;
this is not a strict guaranteed miss-distance bound on varied terrain.

GUN_LIFT increases from 0.90 to 1.10; all floating meshes, rig pivots and the
central charge/muzzle rise together by 0.20 game units. Materials and UVs are
unchanged. A conservative exported-SCM bound, including the lowest hover and
arbitrary pitch/recoil/yaw, gives 0.296 / 0.289 vertical clearance above the highest
foundation vertex for LOD0 / LOD1. Closing the gondolas changes X only and cannot
reduce this vertical clearance. See howitzer_validation.json.

Each autonomous charge costs 2000 energy, including the initial charge without a
target. BeginRecharge uses the native CreateEconomyEvent progress callback, as
used by Unit teleportation, to grow the orb and open the gondolas. The nominal
growth lasts 7.6 seconds after 0.1 seconds delay + 0.3 seconds closing; the average
continuous-fire draw is 250 energy/s. An energy shortage slows the same progress;
the weapon cannot fire until the event completes. Holding an already ready ball
costs no energy. The stock weapon's separate StartEconomyDrain is overridden to
avoid charging twice. Death cancels the event. Weapon adjacency energy modifiers
are read through GetWeaponEnergyRequired. Dry-land hits do not add an impact burst
on top of the six 400-point strikes; shield/water fallback is separately 2400.

The preceding version is archived in before-2026-10-21-howitzer.zip. Geometry,
Lua syntax, economy stall/resume and projectile logic were checked outside the
repo. This version has not been tested in a FAF match.

## Integration with main 82eaab8

The latest upstream units, materials and AI changes are retained. The obsolete
upstream ball mesh is archived in upstream-82eaab8-ball-mesh.zip before removal.
Material mip generation now downsamples each data channel independently, matching
the updated project guide. Ordinary premultiplied RGBA resizing erased metal RGB
under the zero army mask in the old reduced levels. All three mip0 payloads remain
byte-identical; all 11 levels decode, and metal color/reflection survive reduction.
The earlier full-DDS preservation checks describe the preceding revisions, before
this lower-mip correction. No surface artwork or runtime shader is changed here.

## Reference and verification

Inspected installed FAF XSL0401/XSL0402 scripts, XSL0402 blueprint,
`effecttemplates.lua`, Othuy emitters, phason weapon/projectile classes, GameColors,
simInit and blueprint mesh extraction. Engine effect methods were checked against
[upstream IEffect.lua](https://github.com/FAForever/fa/blob/develop/engine/Sim/IEffect.lua).
The empty mesh is confirmed in installed FAF `meshes.nx2`.

`validation.json` records structural checks and mocked Lua checks, including both
central muzzle positions, open ring bores, masks, DDS decoding and resource paths.
Twelve existing projectile checks were rerun outside the repository against the
new scripts and actual effect helper using engine doubles. They cover strike
timing, friendly damage, moving/dead targets, cancellation, lifetime and cleanup.
No test infrastructure was added to the repository.

**This revision has not been run in a FAF match.** Confirm material brightness,
19-color ramp sampling, particle scale, tracking at steep elevations, central
charge/release, shields and ground damage in game. The previous version was tested
by the user and its feedback prompted these changes.

The full preceding runtime resources are preserved in
`archive/before-2026-10-20-corrections.zip` before replacement.

## October 22: initialization hardening and dark stock materials

After user match feedback (no shot, no gondola animation despite energy/valid
range), rotator setters are called separately. CRotateManipulator does not
promise fluent returns. A strict API double returning nil reproduces the old
OnStopBeingBuilt failure at SetTargetSpeed(...):SetAccel(...); the corrected
version completes initial charge, creates a projectile and recharges. Recoil
setter chains are removed too. The user's game.log is not available, so the
specific failure in that match is not yet confirmed by a stack trace.

LOG emits initialization start/completion and only the first ready charge and
first created projectile. These four stage markers allow a game.log to distinguish
an initialization error, stalled charge and firing failure without per-tick logs.

Both LODs now use the native Seraphim shader. The team mask is Albedo.A and is
unchanged spatially. Stock XSB0101/XSB0301/XSB1301 non-team albedo has median RGB
about 16; main turret steel is now about 16, edging about 24, and recessed metal
about 8 after BC3 decoding. Reflectivity remains separate; G is 150–188 for steel.
Colored albedo stays below the Seraphim white-highlight threshold. Shader white
highlights no longer wash out the colored inlays.

The old RGB normal map with alpha=255 was incompatible with mesh.fx ComputeNormal,
which reads .ga for both Unit and Seraphim. Normals now pack the bitangent component
in G and tangent component in A; decoded squared XY length is below one throughout.
The RGB normal remains as GGA2404_normalsTS_authoring.png for Blender. The editable
Blend is repacked with updated images; SCM geometry, bones and UVs are unchanged.
All material mip levels use independent channel reduction. The SCM preview now
decodes packed normals and approximates the Seraphim metallic shading; it is not
a FAF screenshot or proof of game rendering. See charge_dark_validation.json.

Pre-change assets are archived in before-2026-10-22-charge-dark-metal.zip. The
revised initialization/materials have passed file and mocked API checks only.
A match with this revision and the friend's game.log are still needed.

## October 25: confirmed script-load failure and idle rebuild

The local FAF 3840 `game_28011333.log`, lines 985–987, identifies the actual
failure: `gga2404_script.lua(28): ']' expected near 'end'`. The module never
defined `TypeClass`, so the game substituted the generic Unit class. This explains
why the native weapon could aim and play its sound while the custom charge,
animation and projectile behavior were missing. The October 22 rotator change
did not address this parser failure.

The unsupported Lua 5.1 array-length operator is replaced with `table.insert`
in both the gondola array and `lua/vael_itha_effects.lua`. The second occurrence
would otherwise prevent the charge/shot effect module from loading after the
unit script was repaired. Slider setters are now separate calls too; field
rotators are retained in their named list as well as Trash.

Idle hover is rebuilt as a continuous sine wave updated each simulation tick:
±0.08 game units over 40 ticks (4 seconds), instead of two linear moves with
pauses. The vertical Hover bone remains above TurretPitch, and no animator keys
the aiming or muzzle bones. Gondola closure, paid autonomous charge, ready hold,
field rotation and shot recoil keep their existing procedural controllers.
The configured charge remains 2000 energy and the nominal firing cycle 8 seconds.
No replacement full-rig SCA is used: the old clips override aiming and stay obsolete.

`preview_animation.py` reads the exported SCM skeleton and actual runtime DDS,
then generates mechanical cycle frames and front/side/top views in
`animation-rebuild-2026-10-25/`. Run it with Python, numpy and Pillow. These are
illustrative mesh poses, without the engine's particles, economy or firing logic.
SCM and texture geometry/materials did not require regeneration.

Checks recorded in `animation-rebuild-2026-10-25/verification.json`:
all eight relevant Lua/blueprint files compile with Lua 5.1, and their code has no
unsupported length operator; both LODs have the same 12-bone skeleton and matching
Charge/Muzzle origins. Including the larger hover, conservative foundation
clearance is 0.246 / 0.239 game units, and closed gondola clearance is 0.0985.
Compilation with Lua 5.1 is a syntax check, not a substitute for the engine parser.

Previous runtime resources are in `archive/before-2026-10-25-animation-repair.zip`;
the installed previous resources, including obsolete SCA files, are separately
preserved in `archive/installed-before-2026-10-25-animation-repair.zip`.
The complete mod folder is copied for local deployment while preserving unrelated
installed runtime files that differ from ongoing workspace edits. Changed runtime files are compared
by SHA256. **No new match was run:** window control was denied with
`Computer Use was not approved to use forgedalliance`. The old match log proves the
original load failure, not successful firing of this revision. Verify in a fresh
match: initial charge without a target, hover, aiming, ready hold, projectile,
recoil/closing/recharge, energy stall and target/hold-fire changes.
