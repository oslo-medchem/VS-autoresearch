#!/usr/bin/env python3
"""SCAFFOLD ONLY - DO NOT AUTO-RUN. Co-crystal ligand self-redock + pose RMSD.

Addresses reviewer point R1.4 ("no comparison of generated binding modes vs
experimental poses"). The archive stores only aggregate metrics, NOT any docked
pose, so pose accuracy cannot be computed from existing data. This scaffolds a
SMALL, gated redock of the co-crystal ligand(s) back into their own receptor and
computes RMSD to the experimental pose.

Docking is stochastic (random seed) and class-expensive per the compute-gap
policy, so this is proposed, never auto-run. A human must review inputs, confirm
the receptor/box pairing, and launch it (see work/compute-requests.md, REQ-1).

Engine: AutoDock Vina (rigid receptor), matching the campaign's Vina baseline.
Env   : conda activate vina_dock   (vina, meeko, rdkit, openbabel)

Cases available in the archive (confirm receptor/ligand PDB match before running):
  FPR2 : ligand VS-autoresearch/04_receptor_preparation/ligand_FUI_crystal.sdf
         receptor .../receptor_naive.pdbqt   center .../ligand_center.txt (81.893,115.414,96.832)
  CDK2 : pilot/cdk2/crystal_ligand.mol2 (FAP/1H00)   -- confirm receptor+center; the
         6INL receptor is cdk2_autoresearch/02_receptor/receptor_naive.pdbqt but its
         co-crystal ligand is NOT extracted, so 1H00 self-redock needs the 1H00 receptor.
  HIVPR: pilot/hivpr/crystal_ligand.mol2            -- confirm receptor+center.
"""

import argparse
import subprocess
from pathlib import Path

# --- Configure one case per run (paths relative to the unzipped archive) ---
CASES = {
    "fpr2": {
        "ligand_ref": "VS-autoresearch/04_receptor_preparation/ligand_FUI_crystal.sdf",
        # skill (Meeko) receptor: this is the receptor behind all reported FPR2 results
        "receptor": "VS-autoresearch/04_receptor_preparation/receptor_skill.pdbqt",
        "center": (81.893, 115.414, 96.832),  # from ligand_center.txt
        "box": (25.0, 25.0, 25.0),  # baseline 25 A box
    },
    # add "cdk2" / "hivpr" once the matching apo receptor + box centre are confirmed
}


def redock(case_name, archive, out_dir, exhaustiveness=8, seed=42):
    """Prepare ligand pdbqt, run Vina in a box around the crystal centre, RMSD."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    cfg = CASES[case_name]
    archive, out_dir = Path(archive), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ref = archive / cfg["ligand_ref"]
    receptor = archive / cfg["receptor"]
    lig_pdbqt = out_dir / f"{case_name}_ligand.pdbqt"
    docked = out_dir / f"{case_name}_docked.pdbqt"

    # 1. add explicit Hs with 3D coords (this Meeko version requires explicit Hs),
    #    preserving the experimental heavy-atom coordinates.
    ref_mol0 = Chem.MolFromMolFile(str(ref), removeHs=False)
    if ref_mol0 is None:
        raise SystemExit(f"could not read crystal ligand: {ref}")
    ref_h = out_dir / f"{case_name}_ref_H.sdf"
    Chem.MolToMolFile(Chem.AddHs(ref_mol0, addCoords=True), str(ref_h))

    # 2. crystal ligand -> pdbqt (meeko; fall back to OpenBabel if Meeko rejects it)
    try:
        subprocess.run(
            ["mk_prepare_ligand.py", "-i", str(ref_h), "-o", str(lig_pdbqt)], check=True
        )
        if not lig_pdbqt.exists() or lig_pdbqt.stat().st_size == 0:
            raise RuntimeError("meeko produced no pdbqt")
    except Exception as e:
        print(f"meeko prep failed ({e}); falling back to OpenBabel ligand prep")
        subprocess.run(["obabel", str(ref_h), "-O", str(lig_pdbqt)], check=True)

    # 2. rigid Vina redock in a box centred on the crystal ligand
    cx, cy, cz = cfg["center"]
    sx, sy, sz = cfg["box"]
    subprocess.run(
        [
            "vina",
            "--receptor",
            str(receptor),
            "--ligand",
            str(lig_pdbqt),
            "--center_x",
            str(cx),
            "--center_y",
            str(cy),
            "--center_z",
            str(cz),
            "--size_x",
            str(sx),
            "--size_y",
            str(sy),
            "--size_z",
            str(sz),
            "--exhaustiveness",
            str(exhaustiveness),
            "--seed",
            str(seed),
            "--out",
            str(docked),
        ],
        check=True,
    )

    # 3. RMSD of top docked pose vs experimental crystal ligand.
    # Vina writes poses best-first; extract the first MODEL only.
    top_pose = out_dir / f"{case_name}_top.pdbqt"
    buf = []
    for ln in docked.read_text().splitlines(keepends=True):
        if ln.startswith("MODEL") and buf and any(b.startswith("ENDMDL") for b in buf):
            break
        buf.append(ln)
        if ln.startswith("ENDMDL"):
            break
    top_pose.write_text("".join(buf))

    # Prefer OpenBabel obrms (symmetry-aware, tolerant of PDBQT); fall back to RDKit.
    rmsd = None
    try:
        out = subprocess.run(
            ["obrms", str(ref), str(top_pose)],
            capture_output=True,
            text=True,
            check=True,
        )
        rmsd = float(out.stdout.strip().split()[-1])
    except Exception as e:
        print(f"obrms unavailable/failed ({e}); trying RDKit fallback")
        ref_mol = Chem.MolFromMolFile(str(ref), removeHs=True)
        top_mol = Chem.MolFromPDBFile(str(top_pose), removeHs=True)
        if ref_mol is not None and top_mol is not None:
            rmsd = AllChem.GetBestRMS(top_mol, ref_mol)

    if rmsd is None:
        msg = (
            f"{case_name}: docking done ({docked.name}); RMSD not computed "
            "automatically. Compute manually, e.g. `obrms ref top_pose`."
        )
        (out_dir / f"{case_name}_rmsd.txt").write_text(msg + "\n")
        print(msg)
        return None
    (out_dir / f"{case_name}_rmsd.txt").write_text(
        f"{case_name} top-pose RMSD to crystal = {rmsd:.3f} A (seed {seed})\n"
    )
    print(f"{case_name}: top-pose RMSD to crystal = {rmsd:.3f} A  (<2 A = reproduced)")
    return rmsd


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", choices=list(CASES), help="which co-crystal case to redock")
    ap.add_argument("archive", help="path to the unzipped vs_autorearch archive")
    ap.add_argument("out_dir", help="output directory for poses + RMSD")
    ap.add_argument("--exhaustiveness", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    redock(a.case, a.archive, a.out_dir, a.exhaustiveness, a.seed)
