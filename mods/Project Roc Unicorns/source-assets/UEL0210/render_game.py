from pathlib import Path
from scm_preview import render_scm
S=Path(__file__).resolve().parent; scm=S/'game_stage/UEL0210_lod0.scm'
for name,a,e in [('perspective',35,28),('front',0,8),('side',90,8),('top',0,85)]:
 print('Rendering',name,flush=True);render_scm(scm,S,S/('scm_'+name+'.png'),a,e,size=500)
