# Dush'Nai approved hover model and native integration

This directory contains the native export, material, icon and preview tools for
GGA0401 Dush'Nai. The unit keeps the existing Itha-Yen ID and core combat values,
with a replacement eight-petal hover hull and paired open-ring gondolas.

## Editable source and rebuild

Download `Dush_Nai_Model_Source_v23.zip` from the
[v5 preview release](https://github.com/TheGhostOfCommunizm/faf-mods-pack/releases/tag/dush-nai-vael-itha-v5-2026-10-31).
Extract its contents into this directory, placing `approved_hover_v23.blend`
alongside these scripts. The packed Blender source is a release asset rather
than a large Git blob. The ornament mask is also included here.

Requirements: Blender 4.5, Python with numpy and Pillow. From this directory:

```powershell
python rebuild_native.py --blender 'C:/path/to/blender.exe' --previews
```

Sources resolve relative to the checkout; outputs go to the repository's
`outputs/` folder. The rebuild writes this mod's GGA0401 SCM/DDS and optionally
its two construction-icon copies. It does not rewrite Lua or gameplay values.
Preview-only historical charge studies approximate engine beams and lighting;
they are not recordings from FAF. Inspect Blender logs: its process can exit
successfully even when a Python script raised an exception.

## Geometry and materials

Blender (x,y,z) maps to native (x,z,-y)*5; existing UniformScale .1 is retained.
Three native SCM LODs have 50,080 / 26,335 / 14,285 vertices and identical 33-bone
skeletons. Ring-axis pitch and MainMuzzle coincide at native (0,18.2,0).
GondolaLeft/Right allow independent lateral travel. Ten child electrode bones
move with their gondola. Legacy AA bones are unweighted/unused; AA weapons were
removed without rebuilding the accepted rig.

All ornamentation follows army color except fixed violet ring inlay/lining.
The Unit shader is intentional: native Seraphim remaps RGB to a neutral palette
and cannot retain that fixed violet hue. Unit SpecTeam.A is the army mask, B is
emission; normals use packed G/A. Dark-steel palette and roughness are calibrated
from GGA2404's own DDS, with conservative reflectance to avoid bright silver.
Every channel is mipmapped independently before BC3 compression.

Original GGA0401 DDS names remain unchanged: the accepted phason projectile
still samples them. New body textures use `GGA0401_approved_*` names.

## Runtime behavior

`lua/itha_yen_charge.lua` controls visual effects only. An owned, non-colliding
Entity uses the original phason mesh and six stock trail layers as the growing
charge sphere. Full radius .288 fits the .59588 open gap; gondolas close inward
by .215 game units each, leaving a .16588 gap, then reopen with sphere growth.
The charged sphere waits for a target. Violet sheath/white core beams change
endpoints each tick. Death and destruction clean up all effects.

`lua/dush_nai_fire_path.lua` samples terrain every <=.5 units on straight shot
lines. The weapon checks before entering the native salvo/clock and again at
release. Blocked recovery releases the unreachable target; replacement search
uses existing priorities, range, layers and current active intel. No player
orders or vision are changed. This is a terrain check, not a general prop raycast.
Clear shots still use the inherited native weapon lifecycle. A cancellable
native-equivalent progress clock prevents empty repeated reload cycles.

## Validation status

User reports confirm model construction, movement and firing, accepted charge
animation and no-AA removal. Latest targeting/progress recovery, new icon and
Vael-Itha terrain-placement tolerance still need a fresh in-game test.

File checks cover SCM indices/binds/normals/rig, three LODs, open-ring clearance,
DDS mip channels and army masks, fixed violet ring, and matching 64x64 seven-mip
icons in both UI paths. Mocked coroutine/state checks cover blocked-only retries
without clocks, first obstructed target plus an accessible enemy, intel/range/
priority filters, acquisition-cache delay and midcharge cancellation. These
checks do not establish an engine match pass.
