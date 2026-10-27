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

## PR #3 conflict resolution — 2026-10-27

Integrated PR head `7fdf6fc` with main `179cfd0` on the local branch
`codex/pr-3-resolve-conflicts`.

- Retain main's `Project Roc Unicorns` directory and update the PR's newly added
  imports and projectile material/mesh paths. GGP0401 and GGP0401Charge are supplied
  by this mod; Additional Units and its GGA0402 are not dependencies. References
  to GGA0402 above describe the original rebuild's weapon/visual reference.
- Retain the PR's native Phason payment and firing lifecycle, independent visual
  threads, GGP0401 projectile inheritance and half-scale charge/flight mesh.
- Retain main's October 25 parser/API repairs and configurable continuous hover:
  HoverHeight=0.08, HoverPeriodTicks=40, scale conversion and bounded phase.
  Add the PR's VisualScale=0.05 to the same ChargeAnimation table.
- Preserve main's current README and October 25 diagnosis/history, then document
  the combined current behavior. Keep the PR's archived assets and validation
  metadata under the renamed directory. Older validation records describe their
  original revisions, not a fresh run of the combined version.

Checks performed for this merge: Lua 5.1 compilation of ten relevant Lua/blueprint
files; resolution of 26 unique resource references against this repository and
local FAF/base-game archives; blueprint parameter assertions; execution of the
merged hover function for a full four-second period using minimal engine stubs;
byte comparison of every GGA2404 SCM/DDS with main; and diff scope verification.
No changes to other mods are introduced relative to main.
These are file checks and a narrow controller check. Native firing, economy,
rendering, targeting, collision and damage were not re-tested in a FAF match.
