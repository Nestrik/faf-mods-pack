import json, re, zipfile, hashlib
from pathlib import Path

ROOT = Path(r'D:\Games\FafModsCreate')
OUT = ROOT / 'outputs/experimental_units_20261024/work'
MODS = Path(r'D:\Games\FAF Mods\mods')

class Parser:
    def __init__(self, text):
        pattern = r"--\[\[[\s\S]*?\]\]|--[^\n]*|\s+|'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|\[\[[\s\S]*?\]\]|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_][A-Za-z_0-9]*|."
        self.t = [m.group() for m in re.finditer(pattern,text) if not m.group().isspace() and not m.group().startswith('--')]
        self.i=0
    def pop(self):
        x=self.t[self.i]; self.i+=1; return x
    def peek(self, n=0): return self.t[self.i+n] if self.i+n<len(self.t) else ''
    def value(self):
        x=self.pop()
        if x=='{': return self.table()
        if x in ('-', '+'):
            v=self.value(); return -v if x=='-' else v
        if x[0:1] in ('"', "'"):
            return re.sub(r'\\([\\\'"nrt])', lambda m:{'n':'\n','r':'\r','t':'\t'}.get(m[1],m[1]), x[1:-1])
        if x.startswith('[['): return x[2:-2]
        if x=='true': return True
        if x=='false': return False
        if x=='nil': return None
        if re.fullmatch(r'(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?',x):
            n=float(x); return int(n) if n.is_integer() else n
        if self.peek()=='{':
            self.pop(); v=self.table()
            return {'__constructor':x, **v} if isinstance(v,dict) else {'__constructor':x,'__items':v}
        return x
    def table(self):
        vals={}; index=1
        while self.peek()!='}':
            if not self.peek(): raise ValueError('Unclosed table')
            if self.peek() in (',',';'): self.pop(); continue
            if self.peek()=='[':
                self.pop(); key=self.value(); assert self.pop()==']'; assert self.pop()=='='
            elif self.peek(1)=='=':
                key=self.pop(); self.pop()
            else:
                key=index; index+=1
            val=self.value()
            if isinstance(val,(int,float)) and self.peek() in ('+','-','*','/','^'):
                expr=str(val)
                while self.peek() not in (',',';','}') and self.peek(): expr+=self.pop()
                if not re.fullmatch(r'[0-9eE.+*/^() -]+',expr): raise ValueError(expr)
                val=eval(expr.replace('^','**'),{'__builtins__':{}},{})
            if self.peek() not in (',',';','}'):
                raise ValueError(f'Unexpected expression after {key}: {self.t[max(0,self.i-3):self.i+10]}')
            vals[key]=val
        self.pop()
        if vals and all(isinstance(k,int) for k in vals) and list(vals)==list(range(1,len(vals)+1)):
            return list(vals.values())
        return vals
    def parse(self):
        while self.peek() and self.peek()!='{': self.pop()
        assert self.pop()=='{'
        return self.table()

def read(p): return p.read_text(encoding='utf-8-sig',errors='replace')
def parse(s): return Parser(s).parse()
def clean(s): return re.sub(r'<LOC [^>]+>','',s or '')
def flatten(obj,path=''):
    if isinstance(obj,dict):
        if not obj: yield path,'{}'
        for k,v in obj.items(): yield from flatten(v,f'{path}.{k}' if path else str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj,1): yield from flatten(v,f'{path}[{i}]')
    else: yield path,obj

roots=[ROOT/'mods/seraphim-rework']+sorted(MODS.glob('BlackOpsFAF-*'))
units=[]
for root in roots:
    for p in sorted((root/'units').glob('*/*_unit.bp')):
        txt=read(p); uid=p.stem.replace('_unit','')
        cat_text=re.search(r'Categories\s*=\s*\{(.*?)\}',txt,re.S)
        if not cat_text or ('EXPERIMENTAL' not in cat_text[1] and uid!='BAA0401'): continue
        b=parse(txt); cats=b.get('Categories',[])
        if 'EXPERIMENTAL' not in cats and uid!='BAA0401': continue
        helper='INSIGNIFICANTUNIT' in cats or 'DRONE' in cats
        name=clean(b.get('General',{}).get('UnitName','')) or {'BSB0002':'Дочерняя фабрика квантовой арки'}.get(uid,uid)
        script=next(iter([x for x in p.parent.iterdir() if x.name.lower()==f'{uid.lower()}_script.lua']),None)
        units.append(dict(id=uid,name=name,mod=root.name,group='Наш мод' if root.name=='seraphim-rework' else 'BlackOpsFAF',
            faction=b.get('General',{}).get('FactionName',''),description=clean(b.get('Description','')),helper=helper,
            bp=b,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),script=str(script) if script else None))
units.sort(key=lambda u:(u['helper'],u['group']!='Наш мод',u['faction'],u['mod'],u['id']))
assert len(units)==24,[(u['id']) for u in units]
assert sum(not u['helper'] for u in units)==21

# Virtual files from the selected mods first, then installed FAF/game archives.
archive_paths=[]
for base in [Path(r'D:\Games\FAF Cache\gamedata'),Path(r'D:\Steam\steamapps\common\Supreme Commander Forged Alliance\gamedata')]:
    if base.exists(): archive_paths.extend(sorted([p for p in base.iterdir() if p.suffix.lower() in ('.nx5','.scd') and any(w in p.name.lower() for w in ('projectile','lua','unit','effect'))],key=lambda p:(p.suffix!='.nx5',p.name)))
archives=[]
for p in archive_paths:
    try:
        z=zipfile.ZipFile(p); archives.append((p,z,{n.lower().lstrip('/'):n for n in z.namelist()}))
    except zipfile.BadZipFile: pass

def resolve(virt):
    virt=virt.replace('\\','/').lower()
    if virt.startswith('/mods/'):
        parts=virt.strip('/').split('/'); m=next((r for r in roots if r.name.lower()==parts[1]),None)
        if m:
            cur=m
            for part in parts[2:]:
                cur=next((x for x in cur.iterdir() if x.name.lower()==part),cur/part) if cur.is_dir() else cur/part
            if cur.is_file(): return read(cur),str(cur)
    key=virt.lstrip('/')
    for p,z,idx in archives:
        if key in idx: return z.read(idx[key]).decode('utf-8-sig',errors='replace'),str(p)+'!/'+idx[key]
    return None,None

raw=[]; scripts=[]; projectile_records=[]; missing=[]
for u in units:
    for field,val in flatten(u['bp']): raw.append([u['id'],u['name'],'Юнит',u['id'],field,val,type(val).__name__,u['path']])
    if u['script']:
        for line,txt in enumerate(read(Path(u['script'])).splitlines(),1): scripts.append([u['id'],u['name'],'Скрипт юнита',line,txt,u['script']])
    visited=set()
    queue=[]
    for field,val in flatten(u['bp']):
        if isinstance(val,str) and (field.endswith('ProjectileId') or val.lower().endswith('_proj.bp')): queue.append(val)
    while queue:
        virt=queue.pop(0)
        if virt.lower() in visited: continue
        visited.add(virt.lower())
        txt,src=resolve(virt)
        if txt is None: missing.append([u['id'],virt]); continue
        b=parse(txt)
        projectile_records.append({'unit':u['id'],'virtual':virt,'bp':b,'source':src})
        for field,val in flatten(b):
            raw.append([u['id'],u['name'],'Снаряд',virt,field,val,type(val).__name__,src])
            if isinstance(val,str) and val.lower().endswith('_proj.bp'): queue.append(val)
        sv=virt[:-8]+'_script.lua' if virt.lower().endswith('_proj.bp') else ''
        st,ss=resolve(sv)
        if st:
            for line,txt in enumerate(st.splitlines(),1): scripts.append([u['id'],u['name'],'Скрипт снаряда',line,txt,ss])
            for child in re.findall(r"['\"]([^'\"]+_proj\.bp)['\"]",st,re.I): queue.append(child)

# Shared mechanics that change declared combat characteristics.
shared=[MODS/'BlackOpsFAF-Unleashed/lua/BlackOpsdefaultantiprojectile.lua',MODS/'BlackOpsFAF-Unleashed/lua/BlackOpsweapons.lua',
    MODS/'BlackOpsFAF-Unleashed/lua/BlackOpsprojectiles.lua',MODS/'BlackOpsFAF-StellarBuff/hook/lua/system/Blueprints.lua',
    MODS/'BlackOpsFAF-ACUs/units/EEL0001/EEL0001_script.lua',MODS/'BlackOpsFAF-ACUs/units/EEL0001/EEL0001_unit.bp',
    ROOT/'mods/seraphim-rework/hook/lua/system/Blueprints.lua']
for p in shared:
    for line,txt in enumerate(read(p).splitlines(),1): scripts.append(['Общий',p.stem,'Общая механика',line,txt,str(p)])

# Include unit-specific local script modules imported by the selected units.
seen_sources={s[5] for s in scripts}
for u in units:
    if not u['script']: continue
    imports=re.findall(r"import\(['\"]([^'\"]+)['\"]\)",read(Path(u['script'])))
    for virt in imports:
        if not virt.lower().startswith('/mods/'): continue
        txt,src=resolve(virt)
        if txt and src not in seen_sources:
            seen_sources.add(src)
            for line,txt in enumerate(txt.splitlines(),1): scripts.append([u['id'],u['name'],'Импортированная механика',line,txt,src])

data={'units':units,'raw':raw,'scripts':scripts,'projectiles':projectile_records,'missing':missing,'archives':[str(p) for p,z,i in archives]}
(OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'units':len(units),'main':sum(not u['helper'] for u in units),'weapons':sum(len(u['bp'].get('Weapon',[])) for u in units),'raw_fields':len(raw),'script_lines':len(scripts),'projectiles':len(projectile_records),'missing':missing},ensure_ascii=False))
