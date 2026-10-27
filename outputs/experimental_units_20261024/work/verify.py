import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
BASE=Path(r'D:\Games\FafModsCreate\outputs\experimental_units_20261024')
data=json.loads((BASE/'work/data.json').read_text(encoding='utf-8'))
book=BASE/'Экспериментальные_юниты_Seraphim_Rework_и_BlackOpsFAF_обновлено.xlsx'
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(book) as z:
    assert z.testzip() is None
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    def read_sheet(n):
        root=ET.fromstring(z.read(f'xl/worksheets/sheet{n}.xml'))
        cells={}
        for c in root.findall('.//m:sheetData/m:row/m:c',ns):
            v=c.find('m:v',ns); t=c.get('t')
            if t=='inlineStr': value=''.join(c.find('m:is',ns).itertext())
            elif v is None: value=None
            elif t=='s': value=strings[int(v.text)]
            elif t=='b': value=v.text=='1'
            elif t in ('str','e'): value=v.text
            else:
                value=float(v.text)
                if value.is_integer(): value=int(value)
            cells[c.get('r')]=value
        return root,cells
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    names=[s.get('name') for s in wb.find('m:sheets',ns)]
    assert names==['Сравнение','Экономика','Защита','Движение и разведка','Оружие','Примечания'],names
    root,summary=read_sheet(1)
    for r,u in enumerate(data['units'],6):
        assert summary[f'A{r}']==u['id']
        e=u['bp']['Economy']
        for col,k in [('G','BuildCostMass'),('H','BuildCostEnergy'),('I','BuildTime')]:
            assert summary.get(f'{col}{r}')==e.get(k),(u['id'],k)
    defense_root,defense=read_sheet(3)
    by_id={u['id']: (i+6,u) for i,u in enumerate(data['units'])}
    for unit_id,expected in {
        'GGA0401': {'mass':32000,'energy':480000,'build':52000,'hull':8000,'shield':32000,'shield_size':7,'shield_regen':1000,'shield_recharge':20},
        'GGA1401': {'mass':6000,'energy':90000,'build':11000,'hull':24000,'shield':26000,'shield_size':12,'shield_regen':1000,'shield_recharge':10},
    }.items():
        row,u=by_id[unit_id]
        assert summary[f'A{row}']==unit_id
        for col,key in [('G','mass'),('H','energy'),('I','build'),('J','hull'),('K','shield')]:
            assert summary[f'{col}{row}']==expected[key],(unit_id,col,summary.get(f'{col}{row}'),expected[key])
        assert defense[f'A{row}']==unit_id
        for col,key in [('I','shield'),('K','shield_size'),('L','shield_regen'),('N','shield_recharge')]:
            assert defense[f'{col}{row}']==expected[key],(unit_id,col,defense.get(f'{col}{row}'),expected[key])
    economy_root,economy=read_sheet(2)
    reactor_row,_=by_id['GGA1401']
    assert economy[f'J{reactor_row}']==25000,economy.get(f'J{reactor_row}')
    panes=[]
    for i,name in enumerate(names,1):
        rt,cells=read_sheet(i)
        pane=rt.find('.//m:pane',ns)
        panes.append((name,pane.attrib if pane is not None else None))
        if i<8: assert pane is not None and pane.get('ySplit')=='5'
    tables=[n for n in z.namelist() if n.startswith('xl/tables/table') and n.endswith('.xml')]
    assert len(tables)==7,len(tables)
    for path in tables:
        tr=ET.fromstring(z.read(path)); assert tr.find('m:autoFilter',ns) is not None,path
print(json.dumps({'xlsx_valid':True,'sheets':len(names),'tables_with_filters':len(tables),'checked_units':24,'balance_rows_checked':['GGA0401','GGA1401'],'reactor_energy_per_second':25000,'bytes':book.stat().st_size,'panes':panes},ensure_ascii=False))
