"""Two seasonal 3x3x3 WASP experiments; constant-concentration inlet Q scenarios."""
import csv,sys,math,shutil,subprocess,hashlib
import os
from pathlib import Path
from itertools import product
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'06_复现脚本/运行依赖'))
from run_wasp8_p_input_demo import read_final,upstream_dip
from run_course_factorial import mean_water_temperature
from package_seasonal_models import MODELS
BIN=Path(os.environ.get('WASP_BIN', r'D:\APP\USEPA-WASP8\wasp\bin'))
OUT=ROOT/'02_中间输出/07_季节三因素情景'
RES=ROOT/'03_最终结果/04_季节情景与交互'
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    seg=read(ROOT/'01_模型输入/01_segments_uniform_geometry.csv')
    flows=read(ROOT/'01_模型输入/09_WASP_surface_flow_paths.csv')
    vols=[float(r['volume_m3']) for r in seg[:23]]
    weighted=lambda a:sum(x*v for x,v in zip(a[:23],vols))/sum(vols)
    summary=[];profiles=[];interactions=[];qa=[]
    for m in MODELS:
        period=m['season']; folder=OUT/period;folder.mkdir(parents=True,exist_ok=True)
        source=ROOT/'02_中间输出/06_季节独立率定/最终工程'/period
        source_wif=source/(m['stem']+'.wif'); cached_base=folder/'base.wif'
        same_base=cached_base.exists() and cached_base.read_bytes()==source_wif.read_bytes()
        shutil.copy2(source_wif,cached_base)
        old=read_final(source,m['stem']); cases={}
        headq=float(next(r['Q_m3_s'] for r in flows if r['period']==period and r['flow_path_type']=='inlet'))
        temp=mean_water_temperature(period);dip=upstream_dip(period)
        tn={'2020-08':1.0617,'2021-03':1.17}[period];tp={'2020-08':.0102,'2021-03':.0106}[period]
        for t,p,q in product((0,2,4),(1,2,4),(.7,1.,1.3)):
            stem=f'scenario_T{t}_P{p}_Q{int(q*100)}'
            cmd=['PWASPINIT','PLOADWIF base.wif',f'PBRKTF 1 1 1 0 {temp+t:.8f}',f'PBRKTF 1 1 2 90 {temp+t:.8f}',f'PBOUNDFUNC 5 1 1 0 {dip*p:.8f}',f'PBOUNDFUNC 5 1 2 90 {dip*p:.8f}']
            cmd += [f'PINITC 5 {i} {dip*p:.8f}' for i in range(1,30)]
            cmd += [f'PNOQFUNC 1 1 1 0 {headq*q:.8f}',f'PNOQFUNC 1 1 2 90 {headq*q:.8f}','PTFSREFRESH',f'PSAVEWIF {stem}.wif']
            command_path=folder/(stem+'_build.txt');command_text='\n'.join(cmd)+'\n'
            same_commands=command_path.exists() and command_path.read_text(encoding='ascii')==command_text
            solver_log=folder/(stem+'_solver.log')
            reuse=(same_base and same_commands and all((folder/(stem+ext)).exists() for ext in ('.wif','.OUT','.BMD2'))
                   and solver_log.exists() and 'WASP8 run successfully closed out' in solver_log.read_text(encoding='utf8')
                   and os.environ.get('WASP_FORCE')!='1')
            command_path.write_text(command_text,encoding='ascii')
            for exe,suffix,arg in [('wasptool.exe','build',stem+'_build.txt'),('waspccli.exe','solver',stem+'.wif')]:
                log=folder/(stem+'_'+suffix+'.log')
                if reuse:continue
                r=subprocess.run([str(BIN/exe),arg],cwd=folder,capture_output=True,text=True,errors='replace')
                log.write_text(r.stdout+r.stderr,encoding='utf8')
                assert (r.returncode==0 and 'ERROR:' not in r.stdout) if suffix=='build' else 'WASP8 run successfully closed out' in r.stdout
            rows=read_final(folder,stem); vals=[r['Chla_ug_L'] for r in rows];cases[t,p,q]=vals
            en=max(abs(r['TN_mg_N_L']-tn) for r in rows);ep=max(abs(r['TP_mg_P_L']-(tp+(p-1)*dip)) for r in rows)
            assert en<2e-6 and ep<2e-6 and all(math.isfinite(x) and 0<=x<1000 for x in vals),(stem,en,ep)
            if (t,p,q)==(0,1,1.):assert max(abs(a-b['Chla_ug_L']) for a,b in zip(vals,old))<1e-5
            common={'period':period,'T_plus_C':t,'DIP_factor':p,'Q_factor':q}
            summary.append({**common,'temperature_C':temp+t,'inlet_Q_m3_s':headq*q,'inlet_DIP_mgP_L':dip*p,'target_TP_mgP_L':tp+(p-1)*dip,'DIP_load_kg_day':headq*q*dip*p*86.4,'mean23_Chla_ug_L':weighted(vals),'max23_Chla_ug_L':max(vals[:23]),'max29_Chla_ug_L':max(vals),'max23_segment':seg[vals[:23].index(max(vals[:23]))]['segment_id'],'TN_error':en,'TP_error':ep,'wif_sha256':hashlib.sha256((folder/(stem+'.wif')).read_bytes()).hexdigest()})
            for s,r in zip(seg,rows):profiles.append({**common,'segment_id':s['segment_id'],**r})
            print(period,stem,'mean23',round(weighted(vals),3),flush=True)
        base=cases[0,1,1.]
        for r in [r for r in summary if r['period']==period]:
            r['delta_mean23_ug_L']=r['mean23_Chla_ug_L']-weighted(base)
            r['percent_mean23']=100*r['delta_mean23_ug_L']/weighted(base)
        for t,p,q in product((2,4),(2,4),(.7,1.3)):
            a=cases[t,p,q];b=cases[t,p,1.];c=cases[t,1,q];d=cases[0,p,q];e=cases[t,1,1.];f=cases[0,p,1.];g=cases[0,1,q]
            for i in range(29):
                itp=b[i]-e[i]-f[i]+base[i];itq=c[i]-e[i]-g[i]+base[i];ipq=d[i]-f[i]-g[i]+base[i]
                triple=a[i]-b[i]-c[i]-d[i]+e[i]+f[i]+g[i]-base[i]
                net=a[i]-e[i]-f[i]-g[i]+2*base[i]
                assert abs(net-itp-itq-ipq-triple)<1e-10
                interactions.append({'period':period,'T_plus_C':t,'DIP_factor':p,'Q_factor':q,'segment_id':seg[i]['segment_id'],'I_TP_ug_L':itp,'I_TQ_ug_L':itq,'I_PQ_ug_L':ipq,'I_TPQ_ug_L':triple,'net_nonadditivity_ug_L':net})
    write(RES/'季节三因素_情景汇总.csv',summary);write(RES/'季节三因素_逐段输出.csv',profiles);write(RES/'季节三因素_交互分解.csv',interactions)
    for name,data in [('seasonal_scenarios.csv',summary),('seasonal_interactions.csv',interactions)]:write(ROOT/'chart_data'/name,data)
    print('PASS',len(summary),'scenarios',len(profiles),'profiles',len(interactions),'interaction rows')
if __name__=='__main__':main()
