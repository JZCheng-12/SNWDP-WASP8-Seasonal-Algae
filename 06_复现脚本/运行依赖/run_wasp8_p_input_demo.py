"""Read the baseline DIP input and archived WASP OUT/BMD2 endpoint states."""
from __future__ import annotations
import csv,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def upstream_dip(period: str) -> float:
    with (ROOT / "11_EUTRO_state_boundary_and_initial_ASSUMED.csv").open(
        encoding="utf-8-sig", newline=""
    ) as f:
        for row in csv.DictReader(f):
            if (row["period"] == period and row["case"] == "DIP_10pct"
                    and row["WASP_state_variable"] == "Inorganic Phosphate"):
                return float(row["value_mg_L"])
    raise ValueError(f"Missing DIP: {period}")


def read_final(folder: Path, stem: str) -> list[dict[str, float]]:
    out = (folder / f"{stem}.OUT").read_bytes().decode("latin1", "replace").replace("\x00", "")
    match = re.search(r"Number of Segments:\s*(\d+)\s+Output Variables\s*:\s*(\d+)", out)
    if not match:
        raise ValueError(f"No OUT header: {stem}")
    nseg_out, nvar_out = map(int, match.groups())
    iscs = [int(m.group(2)) for m in re.finditer(
        r"^\s*(\d+)\s+(\d+)\s+\d+\s+([^\r\n]+)",
        out[match.end():match.end() + 4800], re.M
    )][:nvar_out]
    needed = (56, 117, 27, 40, 31, 35, 44, 36, 45)
    if len(iscs) != nvar_out or not set(needed).issubset(iscs):
        raise ValueError(f"Missing output states: {stem}")
    b = (folder / f"{stem}.BMD2").read_bytes()
    if b[:4] != b"BMD2":
        raise ValueError(f"Invalid BMD2: {stem}")
    version, nseg, nvar, max_frames, frames = struct.unpack_from("<5I", b, 4)
    if (version, nseg, nvar, frames) != (2, 29, 22, 92):
        raise ValueError(f"Unexpected BMD2 dimensions: {stem}")
    if (nseg, nvar) != (nseg_out, nvar_out):
        raise ValueError(f"OUT/BMD2 mismatch: {stem}")
    offset = 48 + 8 * max_frames + 8 * nseg * nvar + 4 * (frames - 1) * nseg * nvar
    block = struct.unpack_from(f"<{nseg*nvar}f", b, offset)
    if not all(math.isfinite(x) for x in block):
        raise ValueError(f"Non-finite result: {stem}")
    rows = []
    for seg in range(nseg):
        get = lambda isc: block[iscs.index(isc) * nseg + seg]
        rows.append({
            "Chla_ug_L": get(117), "DO_mg_L": get(56),
            "DIP_mg_P_L": get(40),
            "TN_mg_N_L": sum(get(isc) for isc in (27, 31, 35, 36)),
            "TP_mg_P_L": sum(get(isc) for isc in (40, 44, 45)),
        })
    return rows

