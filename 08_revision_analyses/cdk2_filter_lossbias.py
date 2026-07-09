"""Active-vs-decoy loss-bias of the 'skill' (filtered) CDK2 library preparation.

Addresses reviewer points R3.3 (the CDK2 gain is correction of inappropriate
ligand filtering, not docking-parameter optimisation) and R3.4 (compound loss
differs across configurations, making metric comparison unreliable).

The CDK2 baseline used the 'skill' library preparation (drug-likeness / Brenk-
type filtering); the accepted change switched to the 'naive' preparation (all
parseable compounds). We recover exactly which compounds survived each
preparation from the prepared .pdbqt directories, join to the active/decoy
labels, and test whether the filter dropped actives at a different rate than
decoys (Fisher exact test on the naive->skill loss).

Deterministic: directory listing + label join + Fisher exact. No docking.

Inputs:
  cdk2_autoresearch/01_library/library_labels.csv   (compound_id,smiles,label)
  cdk2_autoresearch/01_library/naive/pdbqt/*.pdbqt   (compounds kept by naive prep)
  cdk2_autoresearch/01_library/skill/pdbqt/*.pdbqt   (compounds kept by skill prep)
Output:
  analysis_outputs/cdk2_filter_lossbias.csv
"""

import sys
from pathlib import Path
import pandas as pd
from scipy.stats import fisher_exact

ARCHIVE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ARCHIVE / "analysis_outputs"
OUT.mkdir(parents=True, exist_ok=True)

LIBDIR = ARCHIVE / "cdk2_autoresearch/01_library"
labels = pd.read_csv(LIBDIR / "library_labels.csv")[["compound_id", "label"]]
labels["compound_id"] = labels["compound_id"].astype(str)
label_map = dict(zip(labels["compound_id"], labels["label"]))


def ids_in(pdbqt_dir):
    return {p.stem for p in (LIBDIR / pdbqt_dir / "pdbqt").glob("*.pdbqt")}


naive_ids = ids_in("naive")
skill_ids = ids_in("skill")


def compo(ids, name):
    lab = pd.Series([label_map.get(i) for i in ids])
    unmatched = int(lab.isna().sum())
    a = int((lab == "active").sum())
    d = int((lab == "decoy").sum())
    return {
        "prep": name,
        "n_prepared": len(ids),
        "actives": a,
        "decoys": d,
        "unmatched_ids": unmatched,
    }


full = {
    "prep": "full_library",
    "n_prepared": len(labels),
    "actives": int((labels.label == "active").sum()),
    "decoys": int((labels.label == "decoy").sum()),
    "unmatched_ids": 0,
}
naive = compo(naive_ids, "naive")
skill = compo(skill_ids, "skill")

# compounds present in naive but dropped by skill filter
dropped_ids = naive_ids - skill_ids
dropped = compo(dropped_ids, "dropped_by_skill_filter")

rows = pd.DataFrame([full, naive, skill, dropped])
rows["active_frac"] = (rows["actives"] / (rows["actives"] + rows["decoys"])).round(4)

# Fisher exact: among naive-prepared compounds, is being dropped by the skill
# filter associated with being an active vs a decoy?
#            dropped   kept(=skill)
# actives      a_drop     a_keep
# decoys       d_drop     d_keep
a_keep, d_keep = skill["actives"], skill["decoys"]
a_drop = naive["actives"] - a_keep
d_drop = naive["decoys"] - d_keep
table = [[a_drop, a_keep], [d_drop, d_keep]]
odds, p = fisher_exact(table, alternative="two-sided")

active_loss_rate = a_drop / naive["actives"]
decoy_loss_rate = d_drop / naive["decoys"]

rows.to_csv(OUT / "cdk2_filter_lossbias.csv", index=False)

pd.set_option("display.width", 200)
print("CDK2 library composition by preparation pipeline:\n")
print(rows.to_string(index=False))
print(
    f"\nSkill filter dropped {naive['n_prepared'] - skill['n_prepared']} of "
    f"{naive['n_prepared']} naive-prepared compounds "
    f"({100 * (naive['n_prepared'] - skill['n_prepared']) / naive['n_prepared']:.1f}%)."
)
print(f"  actives dropped: {a_drop}/{naive['actives']} = {100 * active_loss_rate:.1f}%")
print(f"  decoys  dropped: {d_drop}/{naive['decoys']} = {100 * decoy_loss_rate:.1f}%")
print(f"\nFisher exact (drop ~ active/decoy) 2x2 = {table}")
print(f"  odds ratio (active-drop vs decoy-drop) = {odds:.3f}")
print(f"  p = {p:.3e}")
print(
    f"  -> the skill filter removed actives and decoys at "
    f"{'SIGNIFICANTLY DIFFERENT' if p < 0.05 else 'statistically similar'} rates."
)
print(f"\nWrote {OUT / 'cdk2_filter_lossbias.csv'}")
