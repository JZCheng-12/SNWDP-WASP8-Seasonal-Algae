"""Score the post-hoc winter inlet/stoichiometry sensitivity transparently.

This second stage was designed after inspecting the first grid's winter results.
Its spatial folds therefore describe conditional fit robustness, not independent
confirmation of the whole model-development process.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from fit_seasons_spatial_cv import scores, write_csv  # noqa: E402

sys.path.insert(0, str(HERE / "06_复现脚本" / "运行依赖"))
import fit_chla_course_demo as fit  # noqa: E402

RUN = HERE / "02_中间输出" / "06_季节独立率定" / "入口组成探索"
OUT = HERE / "03_最终结果" / "01_率定与检验"
SPLIT = HERE / "01_模型输入" / "Chla图像估读" / "季节内空间四折划分.csv"


def main() -> None:
    fit.OUT = RUN
    with SPLIT.open(encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["period"] == "2021-03"]
    assert len(rows) == 22
    y = [float(r["Chla_ug_L_approx"]) for r in rows]
    candidates = {}
    for inlet in (5.0, 6.0, 7.0):
        stem = f"fit_2021-03_C{inlet:g}_G4_R0p02_KP0p001_KD0p3"
        pred_by_id = {r["station_id_candidate"]: r["modeled_ug_L"]
                      for r in fit.paired("2021-03", stem)}
        candidates[inlet] = [pred_by_id[r["station_id"]] for r in rows]
    folds, heldout, candidate_summary = [], [], []
    for inlet, pred in candidates.items():
        candidate_summary.append({"inlet_Chla_ug_L": inlet, "N_to_C": 0.1,
                                  "C_to_Chla": 25, "growth_d-1": 4, "Topt_C": 20,
                                  "Kd_m-1": 0.3, **scores(y, pred)})
    for fold in range(1, 5):
        train = [i for i, r in enumerate(rows) if int(r["test_fold"]) != fold]
        test = [i for i, r in enumerate(rows) if int(r["test_fold"]) == fold]
        chosen = min(candidates, key=lambda v: (scores([y[i] for i in train],
                     [candidates[v][i] for i in train])["RMSE_ug_L"], v))
        s = scores([y[i] for i in test], [candidates[chosen][i] for i in test])
        folds.append({"fold": fold, "chosen_inlet_Chla_ug_L": chosen,
                      "test_station_range": rows[test[0]]["block_station_range"],
                      "train_n": len(train), "test_n": len(test), **s})
        for i in test:
            r = rows[i]
            heldout.append({"period": "2021-03", "fold": fold,
                            "station_id": r["station_id"], "station_code": r["station_code"],
                            "distance_km": r["distance_km"], "quality_flag": r["quality_flag"],
                            "observed_ug_L_approx": y[i],
                            "heldout_prediction_ug_L": candidates[chosen][i],
                            "chosen_inlet_Chla_ug_L": chosen})
    write_csv(OUT / "冬季入口组成探索_候选方案.csv", candidate_summary)
    write_csv(OUT / "冬季入口组成探索_空间四折逐折评分.csv", folds)
    write_csv(OUT / "冬季入口组成探索_空间四折留出预测.csv", heldout)
    write_csv(OUT / "冬季入口组成探索_全站点最终拟合.csv", [
        {"period": "2021-03", "station_id": r["station_id"],
         "station_code": r["station_code"], "distance_km": r["distance_km"],
         "quality_flag": r["quality_flag"], "observed_ug_L_approx": y[i],
         "final_fitted_ug_L": candidates[7.0][i],
         "final_stem": "fit_2021-03_C7_G4_R0p02_KP0p001_KD0p3"}
        for i, r in enumerate(rows)
    ])
    pooled = scores([r["observed_ug_L_approx"] for r in heldout],
                    [r["heldout_prediction_ug_L"] for r in heldout])
    print("pooled", pooled)
    print("folds", folds)


if __name__ == "__main__":
    main()
