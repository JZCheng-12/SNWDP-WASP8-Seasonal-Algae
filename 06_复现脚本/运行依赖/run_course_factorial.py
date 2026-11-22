"""Read the 29-segment mean water temperature used as seasonal forcing."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def mean_water_temperature(period: str) -> float:
    with (ROOT / "02_flow_mass_balanced_two_cases.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        values = [float(r["temperature_C"]) for r in csv.DictReader(f)
                  if r["period"] == period]
    if len(values) != 29:
        raise ValueError(period)
    return sum(values) / len(values)

