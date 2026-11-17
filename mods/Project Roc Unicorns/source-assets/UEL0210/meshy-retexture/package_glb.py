from pathlib import Path
import struct,json
S=Path(__file__).resolve().parent
src=(S/'chassis_original.glb').read_bytes();n=struct.unpack_from('<I',src,12)[0];g=json.loads(src[20:20+n]);blen=struct.unpack_from('<I',src,20+n)[0];binary=bytearray(src[28+n:28+n+blen]);old=bytes(binary)
while len(binary)%4:binary.append(0)
png=(S/'chassis_repaint_albedo.png').read_bytes();offset=len(binary);binary.extend(png);idx=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(png)})
g['images'][0]={'bufferView':idx,'mimeType':'image/png','name':'Chassis_repaint_albedo'}
m=g['materials'][0];m.pop('normalTexture',None);m.pop('occlusionTexture',None);p=m['pbrMetallicRoughness'];p.pop('metallicRoughnessTexture',None);p['metallicFactor']=.25;p['roughnessFactor']=.72;m['name']='Blue_gray_armor_painted_wheels'
g['buffers'][0]['byteLength']=len(binary)
while len(binary)%4:binary.append(0)
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
out=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(S/'chassis_repaint.glb').write_bytes(out)
# Check each geometry accessor uses precisely the original raw bytes.
for a in g['accessors']:
 v=g['bufferViews'][a['bufferView']];start=v.get('byteOffset',0);end=start+v['byteLength'];assert binary[start:end]==old[start:end]
print('Geometry and UV accessor data: unchanged; triangles:',g['accessors'][0]['count']//3,'new GLB bytes:',len(out))
