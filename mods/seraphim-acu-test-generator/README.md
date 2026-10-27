# Seraphim ACU Test Generator

Adds the same back-slot enhancement to the stock ACUs of all four factions for quick testing: UEF (`UEL0001`), Aeon (`UAL0001`), Cybran (`URL0001`), and Seraphim (`XSL0001`). The original mod name, folder, and UID are retained so this updates the existing mod.

## Test Generator

- **Energy production:** adds 100,000 per second to blueprint base production
- **Mass production:** adds 2,000 per second to blueprint base production
- **Build power:** raises the ACU's base build rate to 2,500; other build-rate buffs still apply
- **Vision range:** increases the ACU's vision radius to 2,000 after the enhancement completes
- **Cost:** 1 mass, 1 energy, 1 build time
- **Visual slot:** back (`Back_Upgrade_B01` for UEF, `Back_Upgrade` for the other factions)

The enhancement is immediately available and has a matching removal enhancement. It occupies the normal back slot and competes with the ACU's other back enhancements. It reuses each ACU's existing back upgrade point and does not add a custom model. Per-unit script hooks use shared handlers to apply production, build-rate, and vision effects. Removal restores blueprint base production and vision and removes only this enhancement's build-rate buff.

Support is limited to these four stock ACU blueprints; replacement commanders from mods such as BlackOps and support commanders (sACUs) are not included.

## Installation

Copy this entire folder into the FAF data `mods` directory and enable **Seraphim ACU Test Generator** in the FAF mod manager or lobby.

## Files

- `hook/lua/system/Blueprints.lua` — adds the enhancement and removal entry to all four ACU blueprints after blueprints load, with faction-specific visuals.
- `hook/units/{uel0001,ual0001,url0001,xsl0001}/*_script.lua` — registers the enhancement handlers on each stock ACU.
- `lua/TestGenerator.lua` — shared production, build-rate, and vision handlers.
- `mod_info.lua` — mod metadata.

## Verification status

The enhancement dispatch, stock back bones, icons, and base build rates were checked against the installed FAF 3840 sources (`units.nx2` and `lua.nx2`). The three newly supported faction scripts were also checked against FAF's `develop` sources. All seven Lua files passed a Lua 5.4 syntax-only check; hook paths and shared imports were checked for all four ACUs. In-game loading, UI display, installation/removal, and coexistence with other enhancements still require a local match with each faction.
