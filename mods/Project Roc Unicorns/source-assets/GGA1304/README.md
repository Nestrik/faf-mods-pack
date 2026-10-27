# GGA1304 materials

Original silver-steel Seraphim materials authored on 22 October 2026.
The existing `zsb1306_lod*.scm` geometry, UV layout and animations are unchanged.
Albedo.A is the player-color mask, SpecTeam.R/G control the metallic finish,
SpecTeam.B controls bloom, and normal components are packed in G/A.

The three PNG files here are the uncompressed sources. Rebuild with
`../material-adjustment-2026-10-22/adjust_materials.py`; the script generates
all three fabricator atlases from its palette and concentric inlay pattern.
It keeps the existing material file names and uses channel-independent DDS
mipmaps. Original textures and bindings are in the sibling material-pass archive.

See that folder's comparison images and validation report. No match was run.
