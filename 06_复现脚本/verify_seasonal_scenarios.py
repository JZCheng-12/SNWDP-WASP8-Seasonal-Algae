import csv,struct,re,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'03_最终结果/04_季节情景与交互'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
s=read(R/'季节三因素_情景汇总.csv');pr=read(R/'季节三因素_逐段输出.csv');ix=read(R/'季节三因素_交互分解.csv')
assert len(s)==54 and len(pr)==1566 and len(ix)==464
qa=[]
for r in s:
 p=r['period'];stem=f"scenario_T{r['T_plus_C']}_P{r['DIP_factor']}_Q{round(float(r['Q_factor'])*100)}"
 folder=ROOT/'02_中间输出/07_季节三因素情景'/p
 assert hashlib.sha256((folder/(stem+'.wif')).read_bytes()).hexdigest()==r['wif_sha256']
 b=(folder/(stem+'.BMD2')).read_bytes();version,n,k,m,f=struct.unpack_from('<5I',b,4)
 times=struct.unpack_from(f'<{m}d',b,48);prev=max(j for j in range(f) if times[j]<times[f-1]-.5)
 out=(folder/(stem+'.OUT')).read_bytes().decode('latin1').replace('\x00','')
 start=re.search(r'Number of Segments:\s*(\d+)\s+Output Variables\s*:\s*(\d+)',out).end()
 iscs=[int(x.group(2)) for x in re.finditer(r'^\s*(\d+)\s+(\d+)\s+\d+\s+([^\r\n]+)',out[start:start+4800],re.M)][:k]
 def frame(j):return struct.unpack_from(f'<{n}f',b,48+8*m+8*n*k+4*j*n*k+4*iscs.index(117)*n)
 delta=max(abs(a-c) for a,c in zip(frame(f-1),frame(prev)))
 qa.append({'period':p,'stem':stem,'last_time_days':times[f-1],'previous_time_days':times[prev],'max_last_day_Chla_change_ug_L':delta,'TN_error':r['TN_error'],'TP_error':r['TP_error']})
 qa[-1]['last_day_change_exceeds_0p01']=delta>=.01
for r in ix:assert abs(float(r['net_nonadditivity_ug_L'])-sum(float(r[k]) for k in ('I_TP_ug_L','I_TQ_ug_L','I_PQ_ug_L','I_TPQ_ug_L')))<1e-9
with (R/'季节三因素_数值核验.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(qa[0]));w.writeheader();w.writerows(qa)
print('PASS: 54 WIF hashes; 1566 profiles; 464 exact interaction decompositions; max final-day change',max(r['max_last_day_Chla_change_ug_L'] for r in qa),'cases exceeding 0.01',sum(r['last_day_change_exceeds_0p01'] for r in qa))
