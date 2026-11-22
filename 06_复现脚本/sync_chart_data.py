"""Synchronize figure inputs from authoritative result tables."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
def main():
    r=ROOT/'03_最终结果/01_率定与检验';d=ROOT/'chart_data';d.mkdir(exist_ok=True)
    pairs={
        'seasonal_cv_heldout.csv':r/'季节独立率定_空间四折留出预测.csv',
        'seasonal_final_fit.csv':r/'季节独立率定_全站点最终拟合.csv',
        'winter_inlet_heldout.csv':r/'冬季入口组成探索_空间四折留出预测.csv',
        'winter_inlet_final_fit.csv':r/'冬季入口组成探索_全站点最终拟合.csv',
        'seasonal_scenarios.csv':ROOT/'03_最终结果/04_季节情景与交互/季节三因素_情景汇总.csv',
        'seasonal_interactions.csv':ROOT/'03_最终结果/04_季节情景与交互/季节三因素_交互分解.csv',
        'segments.csv':ROOT/'01_模型输入/01_segments_uniform_geometry.csv',
        'flow.csv':ROOT/'01_模型输入/02_flow_mass_balanced_two_cases.csv'}
    for name,source in pairs.items():shutil.copy2(source,d/name)
    shutil.copy2(pairs['seasonal_scenarios.csv'],ROOT/'05_report/补充材料_季节三因素情景输入输出与哈希.csv')
    print('Synced',len(pairs),'figure tables and scenario supplement')
if __name__=='__main__':main()
