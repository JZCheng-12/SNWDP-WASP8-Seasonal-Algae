"""Freeze a season-specific spatial four-fold split before the next calibration.

All 29 model segments remain in the WASP simulation.  Candidate observations
from the 23 main-canal target stations (04–26) are held out by blocks; station
27 is the diversion-node candidate and is excluded from Chl-a scoring.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_模型输入" / "Chla图像估读" / "Chla_高清图站点候选_图像估读.csv"
OUTPUT = ROOT / "01_模型输入" / "Chla图像估读" / "季节内空间四折划分.csv"
BLOCKS = ((4, 9), (10, 15), (16, 21), (22, 26))


def main() -> None:
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        source = list(csv.DictReader(handle))
    out = []
    for row in source:
        station = int(row["station_id_candidate"])
        if row["branch"] != "shared_canal" or not 4 <= station <= 26:
            continue
        fold = next(i for i, (lo, hi) in enumerate(BLOCKS, 1) if lo <= station <= hi)
        out.append({
            "period": row["period"],
            "station_id": row["station_id_candidate"],
            "station_code": row["station_code_candidate"],
            "distance_km": row["station_distance_km"],
            "Chla_ug_L_approx": row["Chla_ug_L_approx"],
            "quality_flag": row["quality_flag"],
            "test_fold": fold,
            "block_station_range": f"{BLOCKS[fold-1][0]:02d}–{BLOCKS[fold-1][1]:02d}",
            "usage_rule": "train on other three folds; score only this fold; never tune from test values",
            "observation_status": row["data_status"],
        })
    out.sort(key=lambda r: (r["period"], int(r["station_id"])))
    counts = Counter((r["period"], r["test_fold"]) for r in out)
    assert len(out) == 42, len(out)
    assert [counts["2020-08", f] for f in range(1, 5)] == [5, 5, 6, 4]
    assert [counts["2021-03", f] for f in range(1, 5)] == [5, 6, 6, 5]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    print("summer", [counts["2020-08", f] for f in range(1, 5)])
    print("winter", [counts["2021-03", f] for f in range(1, 5)])


if __name__ == "__main__":
    main()
