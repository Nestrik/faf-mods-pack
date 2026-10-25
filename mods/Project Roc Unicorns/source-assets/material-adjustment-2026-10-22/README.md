# Material pass — 22 October 2026

The user's in-game screenshot showed the custom hulls brighter than stock
Seraphim buildings. The custom hull albedo RGB is now multiplied by 0.76,
environment-reflection R by 0.88 and bloom B by 0.85. Gloss and existing
player-color masks are preserved. The reused stock GGA0102 hull and energy
effects are outside this material pass. Existing geometry, UVs, animations,
gameplay values and scripts are preserved.

GGA1104/GGA1204/GGA1304 have newly authored steel/gunmetal Seraphim atlases in
their existing 4×2 UV layout. Violet paint is replaced by dark steel, silver
edges and concentric inlays. Their existing luminous inserts retain their
positions, with additional thin player-color lines. Both mesh LODs now use
the stock `Seraphim` shader and existing Seraphim lookup. Albedo.A holds the
team mask; SpecTeam.A is zero; normals use G/A. No stock textures were copied.

GGA2301 retains `Unit` and its SpecTeam.A team mask. Its former opaque RGB
normal map is corrected to packed G/A, and material mip generation now resizes
each channel independently. Its preview normal decoding is updated too.

`archive/` contains the actual pre-edit DDS, blueprints, procedural sources
and material PNGs, including the user's existing GGA1401 source changes.
`geometry_animation_script_hashes_before.json` records protected resources.

Run `adjust_materials.py` using the Python/numpy/Pillow environment described
in the project modeling guide. It rebuilds only textures and the fabricator
shader bindings. It uses the updated per-unit procedural sources. GGA2404 was briefly extracted and then returned to Project Roc Unicorns on
25 October 2026. Its older material backup is now under
`source-assets/GGA2404/archive/material-adjustment-2026-10-22/`. This helper no
longer rebuilds it; use its own current authoring sources instead. Historical
aggregate reports retain their original data.
`--preview` renders the actual SCM and DDS at mip0 and mip2, with green/blue
player colors and multiple angles. The comparison's first two columns show
the old and new materials on the same unchanged SCM.

The helper uses Pillow's compiled BC3 encoder and independent per-channel
Lanczos mipmaps. Existing standalone generators also retain their own BC3
writers. Visual previews approximate lighting and cannot confirm the game's
PBR environment reflections, bloom or appearance in a running match.

See `validation.json` for actual DDS checks, unchanged-resource hashes and
installed-copy verification. No game match was launched for this pass.
