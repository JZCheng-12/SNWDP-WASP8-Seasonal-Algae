"""Independently check reported statistics against archived WASP outputs."""
import csv, hashlib, json, math, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'06_复现脚本/运行依赖'))
from run_wasp8_p_input_demo import read_final
from fit_seasons_spatial_cv import scores

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def close(a,b): assert math.isclose(float(a),float(b),rel_tol=1e-7,abs_tol=1e-7),(a,b)

def main():
    checks=[]
    def ok(name,detail): checks.append({'check':name,'status':'PASS','detail':detail})
    seg=read(ROOT/'01_模型输入/01_segments_uniform_geometry.csv')
    vols={r['segment_id']:float(r['volume_m3']) for r in seg[:23]}
    station={r['to_station_id']:i for i,r in enumerate(seg)}
    result=ROOT/'03_最终结果/01_率定与检验'
    summaries=read(result/'季节独立率定_综合指标.csv')
    allfits=read(result/'季节独立率定_全站点最终拟合.csv')
    predictions=read(result/'季节独立率定_空间四折留出预测.csv')
    candidates=read(result/'季节独立率定_候选参数与全样本拟合.csv')
    folds=read(result/'季节独立率定_空间四折逐折评分.csv')
    facts={'seasons':{},'scenarios':[], 'interactions':[]}
    for period in ('2020-08','2021-03'):
        cv=[r for r in predictions if r['period']==period]; y=[float(r['observed_ug_L_approx']) for r in cv]
        fitted=[r for r in allfits if r['period']==period]; s=next(r for r in summaries if r['period']==period)
        calculated=scores(y,[float(r['heldout_prediction_ug_L']) for r in cv])
        baseline=scores(y,[float(r['baseline_train_mean_ug_L']) for r in cv])
        for k in ('RMSE_ug_L','NSE','MAE_ug_L','bias_ug_L'):close(calculated[k],s['cv_'+k])
        close(baseline['RMSE_ug_L'],s['baseline_cv_RMSE_ug_L'])
        fits={}
        folder=ROOT/'02_中间输出/06_季节独立率定/候选工程'
        for candidate in [r for r in candidates if r['period']==period]:
            raw=read_final(folder,candidate['stem'])
            pred={r['station_id']:raw[station[r['station_id']]]['Chla_ug_L'] for r in cv}
            fits[candidate['stem']]=pred
            close(scores(y,[pred[r['station_id']] for r in cv])['RMSE_ug_L'],candidate['RMSE_ug_L'])
        for fold in [r for r in folds if r['period']==period]:
            train=[r for r in cv if r['fold']!=fold['fold']];test=[r for r in cv if r['fold']==fold['fold']]
            best=min(fits,key=lambda stem:(scores([float(r['observed_ug_L_approx']) for r in train],[fits[stem][r['station_id']] for r in train])['RMSE_ug_L'],stem))
            assert best==fold['selected_stem']
            for r in test:close(r['heldout_prediction_ug_L'],fits[best][r['station_id']])
        facts['seasons'][period]={'first_grid':s,'baseline':baseline,'first_grid_cv':calculated}
    ok('first_grid','36 BMD2 candidate scores and 8 fold selections independently recomputed')
    winter=read(result/'冬季入口组成探索_空间四折留出预测.csv')
    winterfit=read(result/'冬季入口组成探索_全站点最终拟合.csv')
    winterc=read(result/'冬季入口组成探索_候选方案.csv')
    winpred={}
    folder=ROOT/'02_中间输出/06_季节独立率定/入口组成探索'
    for c in winterc:
        chla=float(c['inlet_Chla_ug_L']);raw=read_final(folder,f'fit_2021-03_C{chla:g}_G4_R0p02_KP0p001_KD0p3')
        vals={r['station_id']:raw[station[r['station_id']]]['Chla_ug_L'] for r in winter}
        winpred[chla]=vals
        close(scores([float(r['observed_ug_L_approx']) for r in winter],[vals[r['station_id']] for r in winter])['RMSE_ug_L'],c['RMSE_ug_L'])
    for fold in range(1,5):
        train=[r for r in winter if int(r['fold'])!=fold];test=[r for r in winter if int(r['fold'])==fold]
        best=min(winpred,key=lambda v:(scores([float(r['observed_ug_L_approx']) for r in train],[winpred[v][r['station_id']] for r in train])['RMSE_ug_L'],v))
        for r in test:
            close(r['chosen_inlet_Chla_ug_L'],best);close(r['heldout_prediction_ug_L'],winpred[best][r['station_id']])
    ok('winter_inlet','3 BMD2 candidates and 4 fold selections verified')
    facts['seasons']['2021-03']['final_cv']=scores([float(r['observed_ug_L_approx']) for r in winter],[float(r['heldout_prediction_ug_L']) for r in winter])
    facts['seasons']['2020-08']['final_cv']=facts['seasons']['2020-08']['first_grid_cv']
    for period in facts['seasons']:
        rows=[r for r in allfits if r['period']==period] if period=='2020-08' else winterfit
        ys=[float(r['observed_ug_L_approx']) for r in rows];ps=[float(r['final_fitted_ug_L']) for r in rows]
        facts['seasons'][period]['spatial']={'n':len(ys),'observed_mean':statistics.mean(ys),'observed_sd':statistics.stdev(ys),'fitted_mean':statistics.mean(ps),'fitted_sd':statistics.stdev(ps),'fit':scores(ys,ps)}
    res=ROOT/'03_最终结果/04_季节情景与交互'
    ss=read(res/'季节三因素_情景汇总.csv');pr=read(res/'季节三因素_逐段输出.csv');ix=read(res/'季节三因素_交互分解.csv')
    assert (len(ss),len(pr),len(ix))==(54,1566,464)
    key=lambda r:(r['period'],int(r['T_plus_C']),int(r['DIP_factor']),float(r['Q_factor']))
    lookup={key(r):r for r in ss}; profiles={}
    for r in ss:
        p,t,d,q=key(r);stem=f'scenario_T{t}_P{d}_Q{round(q*100)}';folder=ROOT/'02_中间输出/07_季节三因素情景'/p
        assert hashlib.sha256((folder/(stem+'.wif')).read_bytes()).hexdigest()==r['wif_sha256']
        assert 'WASP8 run successfully closed out' in (folder/(stem+'_solver.log')).read_text(encoding='utf-8')
        raw=read_final(folder,stem);matching=[v for v in pr if key(v)==key(r)]
        assert len(matching)==29
        for g,a,b in zip(seg,raw,matching):
            assert b['segment_id']==g['segment_id']
            for k,v in a.items():close(v,b[k])
        profiles[key(r)]={g['segment_id']:v['Chla_ug_L'] for g,v in zip(seg,raw)}
        weighted=sum(raw[i]['Chla_ug_L']*float(g['volume_m3']) for i,g in enumerate(seg[:23]))/sum(vols.values())
        close(weighted,r['mean23_Chla_ug_L'])
        base=float(lookup[p,0,1,1.0]['mean23_Chla_ug_L']);close(weighted-base,r['delta_mean23_ug_L']);close((weighted/base-1)*100,r['percent_mean23'])
        tn={'2020-08':1.0617,'2021-03':1.17}[p];tp=float(r['target_TP_mgP_L'])
        assert max(abs(v['TN_mg_N_L']-tn) for v in raw)<2e-6
        assert max(abs(v['TP_mg_P_L']-tp) for v in raw)<2e-6
        facts['scenarios'].append(r)
    for r in ix:
        p,t,d,q=key(r);segid=r['segment_id'];C=lambda a,b,c:profiles[p,a,b,c][segid]
        expected={'I_TP_ug_L':C(t,d,1)-C(t,1,1)-C(0,d,1)+C(0,1,1),
                  'I_TQ_ug_L':C(t,1,q)-C(t,1,1)-C(0,1,q)+C(0,1,1),
                  'I_PQ_ug_L':C(0,d,q)-C(0,d,1)-C(0,1,q)+C(0,1,1),
                  'I_TPQ_ug_L':C(t,d,q)-C(t,d,1)-C(t,1,q)-C(0,d,q)+C(t,1,1)+C(0,d,1)+C(0,1,q)-C(0,1,1),
                  'net_nonadditivity_ug_L':C(t,d,q)-C(t,1,1)-C(0,d,1)-C(0,1,q)+2*C(0,1,1)}
        for k,v in expected.items():close(v,r[k])
    for p in facts['seasons']:
        for q in (.7,1.3):
            group=[r for r in ix if key(r)==(p,4,4,q) and r['segment_id'] in vols]
            facts['interactions'].append({'period':p,'Q_factor':q,**{k:sum(float(r[k])*vols[r['segment_id']] for r in group)/sum(vols.values()) for k in ('I_TP_ug_L','I_TQ_ug_L','I_PQ_ug_L','I_TPQ_ug_L','net_nonadditivity_ug_L')}})
    ok('scenarios','54 solver logs and hashes, 1566 output profiles, weighted means and nutrient mass closure verified')
    ok('interactions','464 interactions recalculated from underlying scenario outputs')
    pairs=[('seasonal_cv_heldout.csv','季节独立率定_空间四折留出预测.csv'),('seasonal_final_fit.csv','季节独立率定_全站点最终拟合.csv'),('winter_inlet_heldout.csv','冬季入口组成探索_空间四折留出预测.csv'),('winter_inlet_final_fit.csv','冬季入口组成探索_全站点最终拟合.csv')]
    for dest,src in pairs:assert read(ROOT/'chart_data'/dest)==read(result/src)
    assert read(ROOT/'chart_data/seasonal_scenarios.csv')==ss
    assert read(ROOT/'chart_data/seasonal_interactions.csv')==ix
    ok('figure_data','All six plotted source tables equal archived calculation tables')
    output=ROOT/'07_核查记录';output.mkdir(exist_ok=True)
    (output/'report_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
    with (output/'一致性核查.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
    print('PASS:',len(checks),'audit groups; all reported statistics traced to solver outputs')
if __name__=='__main__':main()
