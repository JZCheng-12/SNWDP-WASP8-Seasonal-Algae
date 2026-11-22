"""Exploratory season-specific WASP8 Chl-a calibration with frozen spatial folds.

The figure-digitized observations are approximate. The model grid and folds are
fixed before fold scoring; overall observations informed the exploratory design, so the
four-fold scores are conditional spatial tests, not fully independent evidence.
"""

from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "06_复现脚本" / "运行依赖"))
import fit_chla_course_demo as fit  # noqa: E402

RUN = HERE / "02_中间输出" / "06_季节独立率定" / "候选工程"
RESULT = HERE / "03_最终结果" / "01_率定与检验"
SPLIT = HERE / "01_模型输入" / "Chla图像估读" / "季节内空间四折划分.csv"
PERIODS = ("2020-08", "2021-03")
GRID = tuple(product((0.5, 2.0, 4.0), (20.0, 30.0, 35.0), (0.3, 0.7)))
FIXED = {"inlet_chla_ug_L": 5.0, "respiration_d-1": 0.02,
         "kp_mgP_L": 0.001, "C_to_Chla": 25.0, "N_to_C": 0.15,
         "P_to_C": 0.012}


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def scores(y: list[float], pred: list[float]) -> dict:
    if len(y) != len(pred) or not y:
        raise ValueError("Bad score inputs")
    residual = [p - a for p, a in zip(pred, y)]
    denom = sum((a - statistics.mean(y)) ** 2 for a in y)
    return {"n": len(y), "RMSE_ug_L": math.sqrt(statistics.mean(e*e for e in residual)),
            "MAE_ug_L": statistics.mean(abs(e) for e in residual),
            "bias_ug_L": statistics.mean(residual),
            "NSE": 1 - sum(e*e for e in residual) / denom if denom > 0 else float("nan")}


def main() -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    RESULT.mkdir(parents=True, exist_ok=True)
    fit.OUT = RUN
    with SPLIT.open(encoding="utf-8-sig", newline="") as handle:
        split = list(csv.DictReader(handle))
    split_by_period = {period: [r for r in split if r["period"] == period]
                       for period in PERIODS}
    assert [len(split_by_period[p]) for p in PERIODS] == [20, 22]
    candidate_rows, fold_rows, prediction_rows, final_rows, metric_rows = [], [], [], [], []
    for period in PERIODS:
        candidates: list[dict] = []
        points = split_by_period[period]
        for growth, topt, kd in GRID:
            stem = fit.run_case(period, FIXED["inlet_chla_ug_L"], growth,
                                FIXED["respiration_d-1"], FIXED["kp_mgP_L"], kd, topt)
            got = {r["station_id_candidate"]: r for r in fit.paired(period, stem)}
            assert set(got) == {r["station_id"] for r in points}, (period, stem, set(got))
            y = [float(r["Chla_ug_L_approx"]) for r in points]
            pred = [float(got[r["station_id"]]["modeled_ug_L"]) for r in points]
            assert all(abs(float(got[r["station_id"]]["observed_ug_L_approx"]) - yy) < 1e-6
                       for r, yy in zip(points, y))
            s = scores(y, pred)
            candidates.append({"stem": stem, "growth_d-1": growth, "Topt_C": topt,
                               "Kd_m-1": kd, "pred": pred, **s})
            candidate_rows.append({"period": period, "stem": stem, "growth_d-1": growth,
                                   "Topt_C": topt, "Kd_m-1": kd, **s})
            print(period, len(candidates), "/", len(GRID), stem, "RMSE", round(s["RMSE_ug_L"], 3), flush=True)
        for fold in range(1, 5):
            train = [i for i, r in enumerate(points) if int(r["test_fold"]) != fold]
            test = [i for i, r in enumerate(points) if int(r["test_fold"]) == fold]
            select = min(candidates, key=lambda c: (scores([y[i] for i in train],
                            [c["pred"][i] for i in train])["RMSE_ug_L"], c["stem"]))
            train_s = scores([y[i] for i in train], [select["pred"][i] for i in train])
            test_s = scores([y[i] for i in test], [select["pred"][i] for i in test])
            train_mean = statistics.mean(y[i] for i in train)
            base_s = scores([y[i] for i in test], [train_mean] * len(test))
            fold_rows.append({"period": period, "fold": fold, "test_station_range": points[test[0]]["block_station_range"],
                              "selected_stem": select["stem"], "growth_d-1": select["growth_d-1"],
                              "Topt_C": select["Topt_C"], "Kd_m-1": select["Kd_m-1"],
                              "train_n": len(train), "train_RMSE_ug_L": train_s["RMSE_ug_L"],
                              "test_n": len(test), "test_RMSE_ug_L": test_s["RMSE_ug_L"],
                              "test_MAE_ug_L": test_s["MAE_ug_L"], "test_bias_ug_L": test_s["bias_ug_L"],
                              "test_NSE": test_s["NSE"], "baseline_train_mean_ug_L": train_mean,
                              "baseline_test_RMSE_ug_L": base_s["RMSE_ug_L"]})
            for i in test:
                r = points[i]
                prediction_rows.append({"period": period, "fold": fold, "station_id": r["station_id"],
                                        "station_code": r["station_code"], "distance_km": r["distance_km"],
                                        "quality_flag": r["quality_flag"], "observed_ug_L_approx": y[i],
                                        "heldout_prediction_ug_L": select["pred"][i],
                                        "baseline_train_mean_ug_L": train_mean,
                                        "selected_stem": select["stem"]})
        best = min(candidates, key=lambda c: (c["RMSE_ug_L"], c["stem"]))
        for i, r in enumerate(points):
            final_rows.append({"period": period, "station_id": r["station_id"],
                               "station_code": r["station_code"], "distance_km": r["distance_km"],
                               "quality_flag": r["quality_flag"], "observed_ug_L_approx": y[i],
                               "final_fitted_ug_L": best["pred"][i], "final_stem": best["stem"]})
        cv = [r for r in prediction_rows if r["period"] == period]
        cv_s = scores([float(r["observed_ug_L_approx"]) for r in cv],
                      [float(r["heldout_prediction_ug_L"]) for r in cv])
        base_s = scores([float(r["observed_ug_L_approx"]) for r in cv],
                        [float(r["baseline_train_mean_ug_L"]) for r in cv])
        metric_rows.append({"period": period, "final_stem": best["stem"],
                            "final_growth_d-1": best["growth_d-1"], "final_Topt_C": best["Topt_C"],
                            "final_Kd_m-1": best["Kd_m-1"], "final_fit_RMSE_ug_L": best["RMSE_ug_L"],
                            "final_fit_NSE": best["NSE"], "cv_n": cv_s["n"],
                            "cv_RMSE_ug_L": cv_s["RMSE_ug_L"], "cv_MAE_ug_L": cv_s["MAE_ug_L"],
                            "cv_bias_ug_L": cv_s["bias_ug_L"], "cv_NSE": cv_s["NSE"],
                            "baseline_cv_RMSE_ug_L": base_s["RMSE_ug_L"],
                            "baseline_cv_NSE": base_s["NSE"]})
    write_csv(RESULT / "季节独立率定_候选参数与全样本拟合.csv", candidate_rows)
    write_csv(RESULT / "季节独立率定_空间四折逐折评分.csv", fold_rows)
    write_csv(RESULT / "季节独立率定_空间四折留出预测.csv", prediction_rows)
    write_csv(RESULT / "季节独立率定_全站点最终拟合.csv", final_rows)
    write_csv(RESULT / "季节独立率定_综合指标.csv", metric_rows)
    for row in metric_rows:
        print(row, flush=True)


if __name__ == "__main__":
    main()
