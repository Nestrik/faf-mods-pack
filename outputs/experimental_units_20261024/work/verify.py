import json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
BASE=Path(r'D:\Games\FafModsCreate\outputs\experimental_units_20261024')
data=json.loads((BASE/'work/data.json').read_text(encoding='utf-8'))
book=BASE/'Экспериментальные_юниты_Seraphim_Rework_и_BlackOpsFAF.xlsx'
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
    assert len(names)==8,names
    root,summary=read_sheet(1)
    for r,u in enumerate(data['units'],6):
        assert summary[f'A{r}']==u['id']
        e=u['bp']['Economy']
        for col,k in [('G','BuildCostMass'),('H','BuildCostEnergy'),('I','BuildTime')]:
            assert summary.get(f'{col}{r}')==e.get(k),(u['id'],k)
    root,raw=read_sheet(6)
    for row,source in enumerate(data['raw'],6):
        assert raw[f'A{row}']==source[0]
        assert raw[f'E{row}']==source[4]
        actual=raw.get(f'F{row}'); expected=source[5]
        if expected=='': assert actual in ('',None)
        elif isinstance(expected,(int,float)) and not isinstance(expected,bool): assert abs(actual-expected)<1e-8
        else: assert actual==expected,(row,source[4],actual,expected)
    panes=[]
    for i,name in enumerate(names,1):
        rt,cells=read_sheet(i)
        pane=rt.find('.//m:pane',ns)
        panes.append((name,pane.attrib if pane is not None else None))
        if i<8: assert pane is not None and pane.get('ySplit')=='5'
    tables=[n for n in z.namelist() if n.startswith('xl/tables/table') and n.endswith('.xml')]
    assert len(tables)==9,len(tables)
    for path in tables:
        tr=ET.fromstring(z.read(path)); assert tr.find('m:autoFilter',ns) is not None,path
print(json.dumps({'xlsx_valid':True,'sheets':len(names),'tables_with_filters':len(tables),'checked_units':24,'checked_raw_values':len(data['raw']),'bytes':book.stat().st_size,'panes':panes},ensure_ascii=False))
