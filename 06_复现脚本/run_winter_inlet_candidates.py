"""Reproduce the three winter inlet scenarios before their exploratory scoring."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'06_复现脚本/运行依赖'))
import fit_chla_course_demo as fit
fit.OUT=ROOT/'02_中间输出/06_季节独立率定/入口组成探索'
fit.OUT.mkdir(parents=True,exist_ok=True)
fit.BASE_N_C=.10
for c in (5.,6.,7.):print(fit.run_case('2021-03',c,4.,.02,.001,.3,20.),flush=True)
