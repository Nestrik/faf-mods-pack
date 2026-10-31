# Approved hover model integration plan

Goal: replace only Itha-Yen GGA0401's visual model with approved v23; keep gameplay and existing projectiles unchanged. Work locally on F; no upload.

1. Archive original unit files and gameplay hashes. Export v23 to native SCM v5 with LODs, <=65535 vertices each, identical bone skeletons. Preserve eight-petal silhouette, open gondola rings, symmetry and dark metal.
2. Keep existing required main/AA/hull bones; add GondolaLeft/Right under MainPitch for later animation. Set pivot/muzzle at shared ring center. Preserve original unit blueprint and Lua, projectile models and their existing material maps.
3. Create distinct model-specific DDS materials using Unit shader: SpecTeam.A army mask, B emission, GA normals. This shader permits fixed violet ring emission independently of army color; the Seraphim color remap cannot express that hue. Keep all other decorative color team-controlled.
4. Validate SCM headers, bounds, bind transforms, normals/tangents, bone references and LOD consistency; decode DDS mips; compare unchanged gameplay hashes. Render from exported SCM/DDS, including red army proof and side/top views.
5. Package the whole mod for local installation. Locate installed FAF/game; only claim a game test if run. Do not push.

Execution: inline. Existing local/tank-turret-2026-10-31 branch is dedicated to this task. Narrow artifact checks only; no added test infrastructure. This user-approved integration does not yet redesign firing animation or projectile.


31 October charge-animation extension (user approved): add ten electrode bones,
visual-only electrical field, immediate orb discharge, post-shot inward motion
and progressive reopening; retain native weapons and projectile. Implemented
inline. Mock-scheduler checks and native artifact checks pass. In-game check
pending. Preview renders and installable whole-mod archive remain local on F.
