# Vael-Itha weapon rebuild — 2026-10-24

Goal: use the native Phason weapon lifecycle used by GGA0402. Preserve accepted
material, geometry, range, costs, high arc and three-second ground lightning.

Implementation/checklist:
- Replace custom firing states, ChargeReady and unit-owned economy events with
native StartEconomyDrain, native fire-ready waiting and native projectile creation.
- Explicitly start initial recharge after construction, without needing a target.
- Animate gondolas/visible charge from native recharge and muzzle hooks. Visual
threads cannot deny fire. Nominal growth is eight seconds; on an energy shortage
the full orb waits while native payment continues. Ready visuals survive target loss.
- Reuse the GGP0401 visible mesh, trails/impact effects and charge entity from the
new experimental tank. Preserve GGP2404's high-arc and ground-hazard logic.
- Run the actual installed DefaultProjectileWeapon Lua with engine doubles, not
a replacement weapon implementation: first payment, attack-ground, two shots,
low energy, target loss/hold fire, dead units and visual-failure isolation.
- Check resource paths, Lua, unchanged unit DDS/SCM and existing ground hazards.
Package a full mod and publish a PR. No tests added to the repository. No game
match is claimed without actual execution; the original game.log is unavailable.
