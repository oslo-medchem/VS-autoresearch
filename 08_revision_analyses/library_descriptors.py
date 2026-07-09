#!/usr/bin/env python3
"""Physicochemical description of the screening libraries (actives vs decoys).

Addresses reviewer point R1.4: the actives/decoys libraries are not described in
enough detail to judge dockability. For every library with SMILES available
(CDK2 autoresearch DUD-E set, and the CDK2 and HIV-PR pilot sets) we compute a
standard RDKit descriptor panel per compound and summarise it by label so a
reader can see the drug-like ranges and any active/decoy property mismatch.

Deterministic: RDKit descriptors on existing SMILES. No docking, no randomness.
NOTE: the FPR2 library SMILES files in the archive are null-filled (corrupted),
so FPR2 cannot be profiled here; this is reported as a coverage gap.

Inputs (SMILES + label):
  cdk2_autoresearch/01_library/library_labels.csv
  pilot/cdk2/library/library.csv
  pilot/hivpr/library/library.csv
Outputs:
  analysis_outputs/library_descriptors_percompound.csv
  analysis_outputs/library_descriptors_by_label.csv
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski, QED, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

ARCHIVE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ARCHIVE / "analysis_outputs"
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = [
    ("cdk2_autoresearch", ARCHIVE / "cdk2_autoresearch/01_library/library_labels.csv"),
    ("pilot_cdk2", ARCHIVE / "pilot/cdk2/library/library.csv"),
    ("pilot_hivpr", ARCHIVE / "pilot/hivpr/library/library.csv"),
]


def descriptors(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return {
        "MW": Descriptors.MolWt(m),
        "logP": Crippen.MolLogP(m),
        "HBD": Lipinski.NumHDonors(m),
        "HBA": Lipinski.NumHAcceptors(m),
        "TPSA": rdMolDescriptors.CalcTPSA(m),
        "RotBonds": rdMolDescriptors.CalcNumRotatableBonds(m),
        "AromaticRings": rdMolDescriptors.CalcNumAromaticRings(m),
        "HeavyAtoms": m.GetNumHeavyAtoms(),
        "FormalCharge": Chem.GetFormalCharge(m),
        "QED": QED.qed(m),
        "Fsp3": rdMolDescriptors.CalcFractionCSP3(m),
        "LipinskiViolations": sum(
            [
                Descriptors.MolWt(m) > 500,
                Crippen.MolLogP(m) > 5,
                Lipinski.NumHDonors(m) > 5,
                Lipinski.NumHAcceptors(m) > 10,
            ]
        ),
    }


DESC_COLS = [
    "MW",
    "logP",
    "HBD",
    "HBA",
    "TPSA",
    "RotBonds",
    "AromaticRings",
    "HeavyAtoms",
    "FormalCharge",
    "QED",
    "Fsp3",
    "LipinskiViolations",
]

per_rows = []
n_fail = {}
for lib, path in SOURCES:
    df = pd.read_csv(path)
    fail = 0
    for _, r in df.iterrows():
        d = descriptors(r["smiles"])
        if d is None:
            fail += 1
            continue
        d.update({"library": lib, "compound_id": r["compound_id"], "label": r["label"]})
        per_rows.append(d)
    n_fail[lib] = fail

per = pd.DataFrame(per_rows)
per = per[["library", "compound_id", "label"] + DESC_COLS]
per.to_csv(OUT / "library_descriptors_percompound.csv", index=False)

# summary by library x label: mean +/- std, median
agg = per.groupby(["library", "label"])[DESC_COLS].agg(["mean", "std", "median"])
agg.columns = [f"{c}_{s}" for c, s in agg.columns]
agg = agg.round(3).reset_index()
# add n per group
counts = per.groupby(["library", "label"]).size().rename("n").reset_index()
agg = counts.merge(agg, on=["library", "label"])
agg.to_csv(OUT / "library_descriptors_by_label.csv", index=False)

print("Per-compound descriptors:", len(per), "compounds")
print("Parse failures per library:", n_fail)
print("NaN cells in per-compound table:", int(per[DESC_COLS].isna().sum().sum()))
print("\nMean descriptors by library x label (key columns):")
key = [
    "library",
    "label",
    "n",
    "MW_mean",
    "logP_mean",
    "HBD_mean",
    "HBA_mean",
    "TPSA_mean",
    "RotBonds_mean",
    "QED_mean",
    "FormalCharge_mean",
]
print(agg[key].to_string(index=False))
print(f"\nWrote {OUT / 'library_descriptors_percompound.csv'}")
print(f"Wrote {OUT / 'library_descriptors_by_label.csv'}")
