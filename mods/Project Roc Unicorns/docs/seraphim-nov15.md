# Seraphim update — 2026-11-15

Sha’Veyr (GGA2302): floating three-barrel head, white trim and orbiting fins. Barrel radial thickness is 56.25% of the original; LOD0 1178 triangles, LOD1 454. Three simultaneous 650-damage projectiles every 7 seconds, range 80, speed 30, splash radius 4. Spread now selects points in a radius-3 disk on the ground instead of random pitch/yaw; this is not an exact unit conversion from the former angular spread. Ground alignment, selection frame and tarmac use the centered model. Purple wake and softer lightning accompany the projectile.

Ra’Zlom (GGA0405): six-legged siege experimental with main accelerator and two auxiliary beams, modular construction visuals, walking logic, sounds and wreck assets. Amphibious movement and footprint IgnoreStructures flag are enabled.

Validation: Lua syntax, local resource references, SCM buffers and DDS readability checked before publication. The user has tested preceding local versions. Latest ground-spread logic passed mock surface calculations; the final combined build has not been tested in a fresh match by the assistant. Visual effects and terrain/pathfinding behavior still require game verification.

Local backups and intermediate modeling experiments are intentionally excluded from this PR.
