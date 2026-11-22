"""Collect the two runnable seasonal WASP8 projects and their explicit inputs."""

from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
INTERMEDIATE = HERE / "02_中间输出" / "06_季节独立率定"
DEST = INTERMEDIATE / "最终工程"
PARAM = HERE / "05_report" / "补充材料_季节独立率定参数与工程索引.csv"

MODELS = (
    {"season": "2020-08", "label": "夏季最终展示工程", "subdir": "候选工程",
     "stem": "fit_2020-08_C5_G0p5_R0p02_KP0p001_KD0p7_OT30",
     "chla": 5.0, "nc": 0.15, "growth": 0.5, "topt": 30.0, "kd": 0.7},
    {"season": "2021-03", "label": "冬季入口敏感性展示工程", "subdir": "入口组成探索",
     "stem": "fit_2021-03_C7_G4_R0p02_KP0p001_KD0p3",
     "chla": 7.0, "nc": 0.10, "growth": 4.0, "topt": 20.0, "kd": 0.3},
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    with (HERE / "01_模型输入" / "11_EUTRO_state_boundary_and_initial_ASSUMED.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        baseline = list(csv.DictReader(handle))
    for model in MODELS:
        period = model["season"]
        src = INTERMEDIATE / model["subdir"]
        dst = DEST / period
        dst.mkdir(parents=True, exist_ok=True)
        stem = model["stem"]
        files = [f"{period}_daily_combined_base.wif"] + [f"{stem}{suffix}" for suffix in
            (".wif", ".OUT", ".BMD2", "_build.txt", "_build.log", "_solver.log")]
        for name in files:
            source = src / name
            if not source.exists():
                raise FileNotFoundError(source)
            shutil.copy2(source, dst / name)
        solver = (dst / f"{stem}_solver.log").read_text(encoding="utf-8", errors="replace")
        if "WASP8 run successfully closed out" not in solver:
            raise ValueError(f"Solver closure missing for {stem}")
        # Verify the final output shape with the packaged reader.
        from sys import path as module_path
        module_path.insert(0, str(HERE / "06_复现脚本" / "运行依赖"))
        from run_wasp8_p_input_demo import read_final
        if len(read_final(dst, stem)) != 29:
            raise ValueError(f"Expected 29 final segment values for {stem}")
        n_algae = model["chla"] * .001 * 25 * model["nc"]
        p_algae = model["chla"] * .001 * 25 * .012
        pools = {r["WASP_state_variable"]: float(r["value_mg_L"]) for r in baseline
                 if r["period"] == period and r["case"] == "DIP_10pct"}
        rows.append({
            "period": period, "label": model["label"], "final_stem": stem,
            "WIF_relative_path": f"02_中间输出/06_季节独立率定/最终工程/{period}/{stem}.wif",
            "WIF_SHA256": sha(dst / f"{stem}.wif"),
            "inlet_Chla_ug_L": model["chla"], "C_to_Chla": 25,
            "N_to_C": model["nc"], "P_to_C": .012,
            "algae_N_mg_L": n_algae, "algae_P_mg_L": p_algae,
            "upstream_DON_mg_L": pools["Dissolved Organic Nitrogen"] - n_algae / 2,
            "upstream_detrital_N_mg_L": pools["Detrital Nitrogen"] - n_algae / 2,
            "upstream_DOP_mg_L": pools["Dissolved Organic Phosphorus"] - p_algae / 2,
            "upstream_detrital_P_mg_L": pools["Detrital Phosphorus"] - p_algae / 2,
            "growth_20C_d-1": model["growth"], "optimal_temperature_C": model["topt"],
            "light_attenuation_m-1": model["kd"], "respiration_d-1": .02,
            "P_half_saturation_mgP_L": .001,
            "DIP_fraction_of_TP": .1, "radiation_W_m2": 150,
            "sunlight_fraction": .5,
            "status": "exploratory; season-specific Chl-a figure estimates; winter inlet not directly observed",
        })
    PARAM.parent.mkdir(exist_ok=True)
    with PARAM.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(PARAM)
    for row in rows:
        print(row["period"], row["WIF_SHA256"], row["WIF_relative_path"])


if __name__ == "__main__":
    main()
