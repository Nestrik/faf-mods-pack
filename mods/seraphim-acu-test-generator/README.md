# Seraphim ACU Test Generator

Adds a back-slot enhancement to the Seraphim ACU (`XSL0001`) for quick testing.

## Test Generator

- **Energy production:** 100,000 per second
- **Mass production:** 2,000 per second
- **Build power:** raises the ACU's build rate to 2,500
- **Vision range:** increases the ACU's vision radius to 2,000 after the enhancement completes
- **Cost:** 1 mass, 1 energy, 1 build time
- **Visual slot:** back (`Back_Upgrade`)

The enhancement is immediately available and has a matching removal enhancement. It reuses the ACU's existing back upgrade point and does not add a custom model. A Seraphim ACU script hook applies its resource production, build-rate, and vision effects and restores the base values when the upgrade is removed.

## Installation

Copy this entire folder into the FAF data `mods` directory and enable **Seraphim ACU Test Generator** in the FAF mod manager or lobby.

## Files

- `hook/lua/system/Blueprints.lua` — adds the enhancement to the Seraphim ACU blueprint after blueprints load.
- `hook/units/xsl0001/xsl0001_script.lua` — applies and removes the enhancement's resource production, build-rate, and vision effects.
- `mod_info.lua` — mod metadata.
