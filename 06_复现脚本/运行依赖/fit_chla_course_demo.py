"""Course-level conditional WASP8 Chl-a calibration against digitized Fig. S2.

The high-resolution figure yields candidate station IDs from x coordinates.
Only shared-canal station candidates 04-26 are used here.  The diversion-node
candidate 27 is excluded. The seasonal calibration workflow calls this
module separately for each period.  This is not a field-validated model.
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import statistics
import subprocess
import os
from pathlib import Path

from run_wasp8_p_input_demo import read_final


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "WASP8_课程级Chla率定"
SOURCE = ROOT / "WASP8_Chla_探索试算"
BIN = Path(os.environ.get("WASP_BIN", r"D:\APP\USEPA-WASP8\wasp\bin"))
BASE_C_CHLA = 25.0
BASE_N_C = 0.15
BASE_P_C = 0.012


def seed_pools(period: str, chla: float) -> dict[int, float]:
    with (ROOT / "11_EUTRO_state_boundary_and_initial_ASSUMED.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        old = {r["WASP_state_variable"]: float(r["value_mg_L"])
               for r in csv.DictReader(f)
               if r["period"] == period and r["case"] == "DIP_10pct"}
    n_algae = chla * 0.001 * BASE_C_CHLA * BASE_N_C
    p_algae = chla * 0.001 * BASE_C_CHLA * BASE_P_C
    out = {
        3: old["Dissolved Organic Nitrogen"] - n_algae / 2,
        4: old["Detrital Nitrogen"] - n_algae / 2,
        6: old["Dissolved Organic Phosphorus"] - p_algae / 2,
        7: old["Detrital Phosphorus"] - p_algae / 2,
    }
    if min(out.values()) <= 0:
        raise ValueError(f"Insufficient organic N/P for algae seed {period}: {chla}")
    return out


def run_case(period: str, chla: float, growth: float, respiration: float,
             kp: float, kd: float, topt: float = 20.0) -> str:
    OUT.mkdir(exist_ok=True)
    base_name = f"{period}_daily_combined_base.wif"
    base = OUT / base_name
    template = SOURCE / f"{period}_PHYTO_daily_combined.wif"
    if not base.exists() or base.read_bytes() != template.read_bytes():
        shutil.copyfile(template, base)
    stem = (f"fit_{period}_C{chla:g}_G{growth:g}_R{respiration:g}_"
            f"KP{kp:g}_KD{kd:g}").replace(".", "p")
    if topt != 20.0:
        stem += f"_OT{topt:g}".replace(".", "p")
    pools = seed_pools(period, chla)
    commands = ["PWASPINIT", f"PLOADWIF {base_name}", "PCONSTANTSREFRESH"]
    for isc, value in ((65, BASE_N_C), (66, BASE_P_C), (68, BASE_C_CHLA),
                       (69, growth), (71, topt), (74, respiration), (82, kp)):
        commands.append(f"PCONSTVALUEBYISC {isc} 1 {value:.8f}")
    for sys, value in (*pools.items(), (11, chla)):
        commands += [f"PBOUNDFUNC {sys} 1 1 0 {value:.8f}",
                     f"PBOUNDFUNC {sys} 1 2 90 {value:.8f}"]
        commands += [f"PINITC {sys} {seg} {value:.8f}" for seg in range(1, 30)]
    # Keep the published two-period temperature inputs and fixed radiation;
    # only change the assumed water-column light attenuation parameter.
    commands += [f"PCONSTPARAM {seg} 17 1 {kd:.8f}" for seg in range(1, 30)]
    commands.append(f"PSAVEWIF {stem}.wif")
    (OUT / f"{stem}_build.txt").write_text("\n".join(commands) + "\n", encoding="ascii")
    build = subprocess.run([str(BIN / "wasptool.exe"), f"{stem}_build.txt"],
                           cwd=OUT, capture_output=True, text=True, errors="replace")
    (OUT / f"{stem}_build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode != 0 or "ERROR:" in build.stdout:
        raise RuntimeError(f"WASPTool failed {stem}: {build.stdout[-500:]}")
    run = subprocess.run([str(BIN / "waspccli.exe"), f"{stem}.wif"],
                         cwd=OUT, capture_output=True, text=True, errors="replace")
    (OUT / f"{stem}_solver.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if "WASP8 run successfully closed out" not in run.stdout:
        raise RuntimeError(f"WASP solver did not close: {stem}")
    return stem


def observations(period: str) -> list[dict]:
    with (ROOT / "Chla_图像估读" / "Chla_高清图站点候选_图像估读.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        return [{**r, "distance": float(r["station_distance_km"]),
                 "value": float(r["Chla_ug_L_approx"])}
                for r in csv.DictReader(f) if r["period"] == period]


def paired(period: str, stem: str) -> list[dict]:
    rows = read_final(OUT, stem)
    with (ROOT / "01_segments_uniform_geometry.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        segments = list(csv.DictReader(f))
    modeled = {seg["to_station_id"]: val["Chla_ug_L"]
               for seg, val in zip(segments, rows) if seg["branch"] == "shared_canal"}
    out = []
    for o in observations(period):
        station = o["station_id_candidate"]
        if station not in modeled or o["branch"] != "shared_canal":
            continue
        y = modeled[station]
        out.append({"period": period, "station_id_candidate": station,
                    "distance_km": o["distance"], "observed_ug_L_approx": o["value"],
                    "modeled_ug_L": y, "residual_ug_L": y-o["value"],
                    "quality_flag": o["quality_flag"],
                    "status": "highres_figure_estimate_not_raw"})
    return out


def metrics(rows: list[dict]) -> dict:
    err = [r["residual_ug_L"] for r in rows]
    return {"n": len(rows), "MAE_ug_L": statistics.mean(abs(x) for x in err),
            "RMSE_ug_L": math.sqrt(statistics.mean(x*x for x in err)),
            "bias_ug_L": statistics.mean(err)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", choices=("2020-08", "2021-03"), default="2020-08")
    ap.add_argument("--chla", type=float, default=4.0)
    ap.add_argument("--growth", type=float, default=1.0)
    ap.add_argument("--respiration", type=float, default=0.02)
    ap.add_argument("--kp", type=float, default=0.001)
    ap.add_argument("--kd", type=float, default=0.7)
    ap.add_argument("--topt", type=float, default=20.0)
    a = ap.parse_args()
    stem = run_case(a.period, a.chla, a.growth, a.respiration, a.kp, a.kd, a.topt)
    rows = paired(a.period, stem)
    score = metrics(rows)
    print(stem, score)
    print("S01/S29", read_final(OUT, stem)[0]["Chla_ug_L"],
          read_final(OUT, stem)[-1]["Chla_ug_L"])


if __name__ == "__main__":
    main()
