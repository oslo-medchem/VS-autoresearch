#!/usr/bin/env python3
"""Regenerate FPR2 actives physicochemical descriptors from ChEMBL (deterministic).

Fetches all FPR2 (CHEMBL4227) activities with pChEMBL >= 5 (EC50/IC50/Ki/Kd,
standard_relation '='), dedups to unique molecules, standardizes (strip salts +
neutralize, mirroring curate_actives.py), and computes the SAME RDKit descriptor
panel used for the CDK2/pilot libraries (definitions copied verbatim from
library_descriptors.py so results are directly comparable).

FIDELITY: this is the full ChEMBL active set BEFORE the project's downselect and
PAINS/Brenk filter (which produced the 573 docked skill actives). The docked-subset
SMILES are not in the archive, so this characterises the FPR2 active chemical space
from its defining source query, not the exact 573 molecules docked.
"""
import json, sys, time, urllib.request
from pathlib import Path
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski, QED, rdMolDescriptors, SaltRemover
from rdkit.Chem.MolStandardize import rdMolStandardize
RDLogger.DisableLog("rdApp.*")

# --- descriptor panel: verbatim from scripts/library_descriptors.py ---
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
        "LipinskiViolations": sum([
            Descriptors.MolWt(m) > 500,
            Crippen.MolLogP(m) > 5,
            Lipinski.NumHDonors(m) > 5,
            Lipinski.NumHAcceptors(m) > 10,
        ]),
    }
DESC_COLS = ["MW","logP","HBD","HBA","TPSA","RotBonds","AromaticRings",
             "HeavyAtoms","FormalCharge","QED","Fsp3","LipinskiViolations"]

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://www.ebi.ac.uk/chembl/api/data"
q = ("/activity.json?target_chembl_id=CHEMBL4227&pchembl_value__gte=5"
     "&standard_relation=%3D&standard_type__in=EC50,IC50,Ki,Kd&limit=1000")

mols = {}
url = BASE + q; nrec = 0
while url:
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    for a in d["activities"]:
        nrec += 1
        cid, smi = a.get("molecule_chembl_id"), a.get("canonical_smiles")
        if cid and smi and cid not in mols:
            mols[cid] = smi
    nxt = d["page_meta"].get("next")
    url = ("https://www.ebi.ac.uk" + nxt) if nxt else None
    time.sleep(0.2)
print(f"activity records: {nrec} | unique molecules: {len(mols)}")

remover = SaltRemover.SaltRemover(); uncharger = rdMolStandardize.Uncharger()
rows, fail = [], 0
for cid, smi in mols.items():
    m = Chem.MolFromSmiles(smi)
    if m is None:
        fail += 1; continue
    m = uncharger.uncharge(remover.StripMol(m))
    dd = descriptors(Chem.MolToSmiles(m))
    if dd is None:
        fail += 1; continue
    dd.update({"library": "fpr2_actives_chembl", "compound_id": cid, "label": "active"})
    rows.append(dd)
per = pd.DataFrame(rows)[["library", "compound_id", "label"] + DESC_COLS]
per.to_csv(OUT / "fpr2_actives_descriptors_percompound.csv", index=False)
print(f"descriptors computed: {len(per)} | parse/standardize failures: {fail}")

agg = per.groupby(["library", "label"])[DESC_COLS].agg(["mean", "std", "median"])
agg.columns = [f"{c}_{s}" for c, s in agg.columns]
agg = agg.round(3).reset_index(); agg.insert(2, "n", len(per))
agg.to_csv(OUT / "fpr2_actives_descriptors_by_label.csv", index=False)

key = ["MW","logP","HBD","HBA","TPSA","RotBonds","AromaticRings","QED","Fsp3","FormalCharge","LipinskiViolations"]
print("\nFPR2 actives (ChEMBL CHEMBL4227, pChEMBL>=5, salt-stripped+neutralised) descriptor summary:")
print(f"  n = {len(per)}")
for c in key:
    print(f"  {c:18s} mean {per[c].mean():8.3f}  median {per[c].median():8.3f}  std {per[c].std():7.3f}")
print(f"\nWrote {OUT/'fpr2_actives_descriptors_by_label.csv'}")
