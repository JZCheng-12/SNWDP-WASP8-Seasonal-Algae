"""Algebraic diagnostics of existing scenarios; not a new kinetic-budget output."""
import csv,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'03_最终结果/04_季节情景与交互'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
s=read(R/'季节三因素_情景汇总.csv');pr=read(R/'季节三因素_逐段输出.csv');g=read(ROOT/'chart_data/segments.csv')
vol={r['segment_id']:float(r['volume_m3']) for r in g[:23]}
models={r['period']:r for r in read(ROOT/'05_report/补充材料_季节独立率定参数与工程索引.csv')}
common=read(ROOT/'01_模型输入/共用参数参考/补充材料_WASP8季节模型完整参数总表.csv')
out=[]
for r in s:
 p=r['period'];dt=float(r['T_plus_C']);temp=float(r['temperature_C']);t0=temp-dt;opt=float(models[p]['optimal_temperature_C'])
 constants={x['parameter_code']:float(x['value']) for x in common if x['category']=='WASP动力学常数' and x['period']==p}
 assert constants['CONST_ISC_70']<=1
 shape=lambda t:constants['CONST_ISC_72' if t<=opt else 'CONST_ISC_73']
 a=[x for x in pr if all(x[k]==r[k] for k in ('period','T_plus_C','DIP_factor','Q_factor')) and x['segment_id'] in vol]
 wm=lambda k:sum(float(x[k])*vol[x['segment_id']] for x in a)/sum(vol.values())
 out.append({**{k:r[k] for k in ('period','T_plus_C','DIP_factor','Q_factor','mean23_Chla_ug_L')},
 'growth_temperature_shape_ratio_vs_season_base':math.exp(-shape(temp)*(temp-opt)**2+shape(t0)*(t0-opt)**2),
 'respiration_temperature_ratio_vs_season_base':constants['CONST_ISC_75']**dt,
 'mean23_residual_DIP_mgP_L':wm('DIP_mg_P_L'),
 'interpretation':'temperature shape ratio only; not net growth or integrated flux attribution'})
with (R/'季节机制诊断_温度曲线与残余磷.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
for r in out:
 if r['Q_factor']=='1.0' and r['DIP_factor'] in ('1','4'):print(r)
