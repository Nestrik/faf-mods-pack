from pathlib import Path
import struct,math
u=Path(r'D:/Games/FafModsCreate/mods/uef-extra-unit/units/UEL0213')
o=Path(r'D:/Games/FafModsCreate/mods/uef-extra-unit/source-assets/UEL0213')
b=bytearray((u/'UEL0213_lod0.scm').read_bytes()); h=struct.unpack_from('<4s11I',b); vo,n=h[4],h[6]
py,pz=.95,-1.44;c=math.cos(math.radians(-80));s=math.sin(math.radians(-80))
for i in range(n):
 a=vo+i*68
 if b[a+64]!=1:continue
 x,y,z=struct.unpack_from('<3f',b,a); y-=py;z-=pz
 struct.pack_into('<3f',b,a,x,py+c*y-s*z,pz+s*y+c*z)
 for offset in (12,24,36):
  a1,a2,a3=struct.unpack_from('<3f',b,a+offset)
  struct.pack_into('<3f',b,a+offset,a1,c*a2-s*a3,s*a2+c*a3)
p=u/'preview_deployed.scm';p.write_bytes(b)
src=Path(r'D:/Games/FafModsCreate/mods/uef-extra-unit/source-assets/UEL0213/scm_preview.py').read_text().replace('UEL0210','UEL0213')
ns={'__name__':'preview_util'};exec(compile(src,'preview_util','exec'),ns)
ns['render_scm'](p,o,o/'assembled_deployed_scm.png',35,28,size=550)
p.unlink()


