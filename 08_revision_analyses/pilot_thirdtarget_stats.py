#!/usr/bin/env python3
"""Third-target (HIV-PR) scoring-function generalisation from the pilot data.

Addresses reviewer points R1.3 ("only two examples / anecdotal") and R3.7
(generalisation) by summarising the pilot screen, which includes a THIRD target
(HIV protease) in addition to CDK2, both scored with Vina and Vinardo. We
recompute the Vinardo-minus-Vina deltas per target and metric to show, on an
independent target, the same AUC-vs-early-enrichment divergence that the main
campaign reports.

Deterministic: reads existing pilot_results.csv, no docking, no randomness.
Input : <archive>/pilot/pilot_results.csv
Output: analysis_outputs/pilot_scoring_deltas.csv
"""

import sys
from pathlib import Path
import pandas as pd

ARCHIVE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ARCHIVE / "analysis_outputs"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ARCHIVE / "pilot" / "pilot_results.csv")
metrics = ["auc", "bedroc", "ef1"]

rows = []
for target, g in df.groupby("target"):
    g = g.set_index("scoring")
    if not {"vina", "vinardo"}.issubset(g.index):
        continue
    rec = {
        "target": target,
        "n_scored_vina": int(g.loc["vina", "n_scored"]),
        "n_scored_vinardo": int(g.loc["vinardo", "n_scored"]),
    }
    for m in metrics:
        v_vina = float(g.loc["vina", m])
        v_vinardo = float(g.loc["vinardo", m])
        rec[f"{m}_vina"] = round(v_vina, 4)
        rec[f"{m}_vinardo"] = round(v_vinardo, 4)
        rec[f"{m}_delta"] = round(v_vinardo - v_vina, 4)
        rec[f"{m}_pct"] = round(100.0 * (v_vinardo - v_vina) / v_vina, 1)
    rows.append(rec)

out = pd.DataFrame(rows)
out.to_csv(OUT / "pilot_scoring_deltas.csv", index=False)

pd.set_option("display.width", 200)
print("Pilot scoring-function comparison (Vinardo vs Vina), per target:\n")
print(out.to_string(index=False))
print("\nInterpretation (deterministic read):")
for _, r in out.iterrows():
    auc_dir = "up" if r["auc_delta"] > 0 else "down"
    ef_dir = "up" if r["ef1_delta"] > 0 else "down"
    print(
        f"  {r['target']}: AUC {auc_dir} ({r['auc_delta']:+.4f}), "
        f"BEDROC {r['bedroc_delta']:+.4f}, EF1% {r['ef1_delta']:+.4f} "
        f"-> AUC and early-enrichment move {'together' if (r['auc_delta'] > 0) == (r['ef1_delta'] > 0) else 'in OPPOSITE directions'}"
    )
print(f"\nWrote {OUT / 'pilot_scoring_deltas.csv'}")
