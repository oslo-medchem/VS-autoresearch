#!/usr/bin/env python3
"""
CDK2 Autoresearch – Fixed infrastructure (never modified by agent).

Setup NVMe cache, load labels, parse Uni-Dock results, evaluate metrics.
"""

import csv
import os
import shutil
import numpy as np
from pathlib import Path

from sklearn.metrics import roc_auc_score
from rdkit.ML.Scoring import Scoring as RDKitScoring

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent

LABELS_SRC = REPO_ROOT / "01_library" / "labels.csv"
LIBRARY_NAIVE_SRC = REPO_ROOT / "01_library" / "naive" / "pdbqt"
LIBRARY_SKILL_SRC = REPO_ROOT / "01_library" / "skill" / "pdbqt"
RECEPTOR_NAIVE_SRC = REPO_ROOT / "02_receptor" / "receptor_naive.pdbqt"
RECEPTOR_SKILL_SRC = REPO_ROOT / "02_receptor" / "receptor_skill.pdbqt"

# Cache on fast local storage (configurable via environment variable)
CACHE_DIR = Path(os.environ.get(
    "VS_CACHE_DIR",
    str(Path.home() / "vs_cache" / "cdk2")
))
RECEPTOR_NAIVE = CACHE_DIR / "receptor_naive.pdbqt"
RECEPTOR_SKILL = CACHE_DIR / "receptor_skill.pdbqt"
LIBRARY_NAIVE = CACHE_DIR / "library_naive"
LIBRARY_SKILL = CACHE_DIR / "library_skill"
LABELS_CSV = CACHE_DIR / "labels.csv"
RESULTS_DIR = CACHE_DIR / "results"

UNIDOCK_BIN = os.environ.get("UNIDOCK_BIN", shutil.which("unidock") or "unidock")

# CDK2 binding site center (from 6INL co-crystal ligand AJR)
BOX_CENTER = (-11.793, -9.878, -10.380)


# ── Cache setup ──────────────────────────────────────────────────────────────

def setup_cache():
    """Copy receptors + labels to cache, copy PDBQT libraries."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Copy receptors
    for src, dst in [(RECEPTOR_NAIVE_SRC, RECEPTOR_NAIVE),
                     (RECEPTOR_SKILL_SRC, RECEPTOR_SKILL)]:
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {src.name} → {dst}")
        else:
            print(f"  Already cached: {dst.name}")

    # Copy labels
    if not LABELS_CSV.exists():
        shutil.copy2(LABELS_SRC, LABELS_CSV)
        print(f"  Copied labels → {LABELS_CSV}")
    else:
        print(f"  Already cached: labels.csv")

    # Copy PDBQT libraries to cache (avoids slow FUSE I/O)
    for src, dst in [(LIBRARY_NAIVE_SRC, LIBRARY_NAIVE),
                     (LIBRARY_SKILL_SRC, LIBRARY_SKILL)]:
        if not dst.exists():
            print(f"  Copying {src.name} → {dst} (may take a few minutes)...")
            shutil.copytree(src, dst)
            print(f"  Copied {dst.name}")
        else:
            print(f"  Already cached: {dst.name}")

    # Print library counts
    for name, lib_dir in [("naive", LIBRARY_NAIVE), ("skill", LIBRARY_SKILL)]:
        n = len(list(lib_dir.glob("*.pdbqt")))
        print(f"  Library {name}: {n} ligands")

    # Print label counts
    labels = load_labels()
    n_act = sum(1 for v in labels.values() if v == 1)
    n_dec = sum(1 for v in labels.values() if v == 0)
    print(f"  Labels: {n_act} actives, {n_dec} decoys, {len(labels)} total")


# ── Label loading ────────────────────────────────────────────────────────────

def load_labels():
    """Return {compound_id: 0/1} from labels.csv."""
    labels = {}
    with open(LABELS_CSV) as f:
        for row in csv.DictReader(f):
            labels[row["compound_id"]] = 1 if row["label"] == "active" else 0
    return labels


# ── Score parsing ────────────────────────────────────────────────────────────

def parse_unidock_results(results_dir):
    """
    Parse Uni-Dock PDBQT output files → {compound_id: score}.

    Scores are negated so higher = better (more likely active).
    Raw Vina scores are negative kcal/mol; best binding = most negative.
    """
    scores = {}
    n_outliers = 0
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"  WARNING: Results directory not found: {results_path}")
        return scores

    for pdbqt_file in results_path.glob("*.pdbqt"):
        cid = pdbqt_file.stem.removesuffix("_out")
        file_scores = []
        with open(pdbqt_file) as f:
            for line in f:
                if line.startswith("REMARK VINA RESULT:"):
                    parts = line.strip().split()
                    try:
                        s = float(parts[3])
                        if -30.0 <= s <= 0.0:
                            file_scores.append(s)
                        else:
                            n_outliers += 1
                    except (IndexError, ValueError):
                        pass
        if file_scores:
            # Negate: more negative raw = better binding → higher score
            scores[cid] = -min(file_scores)

    if n_outliers > 0:
        print(f"  WARNING: Filtered {n_outliers} corrupted scores (outside -30..0 range)")
    return scores


# ── Ligand index generation ──────────────────────────────────────────────────

def write_ligand_index(library_dir, output_path):
    """Generate ligand_index.txt for Uni-Dock (one PDBQT path per line)."""
    library_dir = Path(library_dir)
    pdbqt_files = sorted(library_dir.glob("*.pdbqt"))
    with open(output_path, "w") as f:
        for p in pdbqt_files:
            f.write(f"{p.resolve()}\n")
    print(f"  Wrote ligand index: {len(pdbqt_files)} ligands → {output_path}")
    return len(pdbqt_files)


# ── Evaluation ───────────────────────────────────────────────────────────────

def calc_bedroc(y_true, y_score, alpha=80.5):
    """BEDROC using RDKit. y_score higher = better."""
    order = np.argsort(-np.array(y_score))
    sorted_data = [[float(y_score[i]), int(y_true[i])] for i in order]
    return RDKitScoring.CalcBEDROC(sorted_data, col=1, alpha=alpha)


def calc_enrichment_factor(y_true, y_score, fraction):
    """Enrichment factor at given fraction of library."""
    y_true = np.array(y_true)
    y_score = np.array(y_score)
    n = len(y_true)
    n_actives = y_true.sum()
    if n_actives == 0:
        return 0.0
    order = np.argsort(-y_score)
    y_sorted = y_true[order]
    n_top = max(1, int(n * fraction))
    actives_in_top = y_sorted[:n_top].sum()
    expected = n_actives * fraction
    return float(actives_in_top / expected) if expected > 0 else 0.0


def evaluate(scores, labels=None):
    """
    Compute VS metrics. Prints parseable lines for agent to grep.

    Args:
        scores: {compound_id: score} where higher = better
        labels: {compound_id: 0/1} or None (auto-loaded)

    Returns:
        dict with auc, bedroc, ef1
    """
    if labels is None:
        labels = load_labels()

    # Align scores with labels
    common = sorted(set(scores.keys()) & set(labels.keys()))
    if len(common) < 100:
        print(f"ERROR: Only {len(common)} compounds have both scores and labels")
        return {"auc": 0.0, "bedroc": 0.0, "ef1": 0.0}

    y_true = [labels[c] for c in common]
    y_score = [scores[c] for c in common]

    n_scored = len(common)
    n_act = sum(y_true)
    n_dec = n_scored - n_act

    # Core metrics
    auc_val = float(roc_auc_score(y_true, y_score))
    bedroc_val = float(calc_bedroc(y_true, y_score, alpha=80.5))
    ef1_val = float(calc_enrichment_factor(y_true, y_score, 0.01))

    # Print parseable lines (agent greps these)
    print(f"auc: {auc_val:.4f}")
    print(f"bedroc: {bedroc_val:.4f}")
    print(f"ef1: {ef1_val:.2f}")
    print(f"scored: {n_scored} ({n_act} actives, {n_dec} decoys)")

    return {"auc": auc_val, "bedroc": bedroc_val, "ef1": ef1_val}


# ── Main (standalone cache setup) ───────────────────────────────────────────

if __name__ == "__main__":
    print("=== CDK2 Autoresearch Cache Setup ===")
    setup_cache()
    print("\nDone. Cache ready at:", CACHE_DIR)
