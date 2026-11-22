"""Refresh file integrity inventory for this release or an explicitly given root."""
import csv,hashlib,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
rows=[]
for p in sorted(root.rglob('*')):
 if not p.is_file() or any(x in p.parts for x in ('__pycache__','.git','_qa_render','.venv')) or p.name=='文件清单与校验值.csv' or p.name.startswith('~$') or '原图' in p.name:continue
 rows.append({'relative_path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with (root/'文件清单与校验值.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['relative_path','bytes','sha256']);w.writeheader();w.writerows(rows)
print(root.name,len(rows),'files',round(sum(r['bytes'] for r in rows)/1048576,1),'MiB')
