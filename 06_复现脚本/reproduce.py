"""One entry point: check archived outputs, rebuild deliverables, or rerun WASP."""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'06_复现脚本'
def run(name):
    subprocess.run([sys.executable,str(SCRIPTS/name)],cwd=ROOT,check=True)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['check','report','full'],nargs='?',default='check')
    ap.add_argument('--skip-plots',action='store_true',help='reuse the supplied figures when R is unavailable')
    args=ap.parse_args()
    if args.mode=='full':
        for name in ('fit_seasons_spatial_cv.py','run_winter_inlet_candidates.py','score_winter_inlet_exploration.py','package_seasonal_models.py','run_seasonal_scenarios.py'):run(name)
    if args.mode!='check':run('sync_chart_data.py')
    run('audit_project.py');run('verify_seasonal_scenarios.py')
    if args.mode!='check':
        run('build_parameter_appendix.py');run('diagnose_seasonal_mechanisms.py')
        if not args.skip_plots:
            r=os.environ.get('RSCRIPT') or shutil.which('Rscript')
            if not r:
                candidates=sorted(Path('C:/Program Files/R').glob('R-*/bin/Rscript.exe'))
                r=str(candidates[-1]) if candidates else None
            if not r:raise SystemExit('Rscript not found. Set RSCRIPT or use --skip-plots.')
            for name in ('plot_seasonal_calibration.R','plot_seasonal_scenarios.R'):
                subprocess.run([r,str(SCRIPTS/name)],cwd=ROOT,check=True)
        run('build_submission_report.py')
    run('refresh_manifest.py')
if __name__=='__main__':main()
