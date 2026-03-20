#!/usr/bin/env python3
"""
VS Autoresearch – Experiment file (agent-modified).

This file defines the docking configuration and execution pipeline.
The agent modifies CONFIG and processing logic to maximize ROC AUC.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path
from scipy.stats import zscore as scipy_zscore

from prepare import (
    CACHE_DIR, RESULTS_DIR, UNIDOCK_BIN, BOX_CENTER,
    RECEPTOR_NAIVE, RECEPTOR_SKILL,
    LIBRARY_NAIVE, LIBRARY_SKILL,
    load_labels, parse_unidock_results, evaluate, write_ligand_index,
)

# ── Tunable configuration ────────────────────────────────────────────────────
# The agent modifies these values to optimize ROC AUC.

CONFIG = {
    # Library choice: "skill" (5223 ligands, Meeko-prepared) or "naive" (10752, OpenBabel)
    "library": "skill",

    # Receptor choice: "skill" (Meeko mk_prepare_receptor) or "naive" (OpenBabel)
    "receptor": "skill",

    # Search box (angstroms) centered on FPR2 binding site
    "box_size": 25,

    # Sampling thoroughness (higher = more exhaustive, slower)
    # Default 8 for fast iteration (~5min). Increase to 32 for production quality.
    "exhaustiveness": 8,

    # Number of binding modes to generate per ligand
    "num_modes": 10,

    # Energy range for keeping poses (kcal/mol above best)
    "energy_range": 3,

    # Scoring function: "vina" or "vinardo"
    "scoring": "vinardo",

    # GPU device index
    "gpu_device": "0",

    # Post-processing score transform: "none", "rank", "zscore", "minmax"
    "score_transform": "none",

    # Batch size for Uni-Dock (smaller = fewer ligands lost per segfault)
    "batch_size": 100,

    # Skip docking and reuse existing results (for testing score transforms)
    "reuse_results": False,
}


# ── Docking execution ────────────────────────────────────────────────────────

def get_library_dir():
    """Return library directory based on CONFIG."""
    return LIBRARY_SKILL if CONFIG["library"] == "skill" else LIBRARY_NAIVE


def get_receptor_path():
    """Return receptor PDBQT path based on CONFIG."""
    return RECEPTOR_SKILL if CONFIG["receptor"] == "skill" else RECEPTOR_NAIVE


def run_docking():
    """
    Execute Uni-Dock with current CONFIG. Returns elapsed seconds.

    Uses batched execution to avoid Uni-Dock segfaults on large libraries.
    """
    # Clean results directory
    if RESULTS_DIR.exists():
        shutil.rmtree(RESULTS_DIR)
    RESULTS_DIR.mkdir(parents=True)

    # Generate ligand index
    index_path = CACHE_DIR / "ligand_index.txt"
    n_ligands = write_ligand_index(get_library_dir(), index_path)

    # Read index lines for batching
    lines = [l for l in index_path.read_text().splitlines() if l.strip()]
    batch_size = CONFIG["batch_size"]

    # Build batch index files
    batch_dir = CACHE_DIR / "batches"
    if batch_dir.exists():
        shutil.rmtree(batch_dir)
    batch_dir.mkdir()

    batches = []
    for i in range(0, len(lines), batch_size):
        bp = batch_dir / f"batch_{i:05d}.txt"
        bp.write_text("\n".join(lines[i:i + batch_size]) + "\n")
        batches.append(bp)

    print(f"  {n_ligands} ligands in {len(batches)} batches of {batch_size}")

    # Environment
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = CONFIG["gpu_device"]

    # Box parameters
    cx, cy, cz = BOX_CENTER
    sz = str(CONFIG["box_size"])

    # Build base command
    base_cmd = [
        UNIDOCK_BIN,
        "--receptor", str(get_receptor_path()),
        "--center_x", str(cx),
        "--center_y", str(cy),
        "--center_z", str(cz),
        "--size_x", sz, "--size_y", sz, "--size_z", sz,
        "--exhaustiveness", str(CONFIG["exhaustiveness"]),
        "--num_modes", str(CONFIG["num_modes"]),
        "--energy_range", str(CONFIG["energy_range"]),
        "--dir", str(RESULTS_DIR),
        "--verbosity", "0",
    ]

    # Add scoring function if not default vina
    if CONFIG["scoring"] != "vina":
        base_cmd.extend(["--scoring", CONFIG["scoring"]])

    t0 = time.time()

    for j, batch in enumerate(batches):
        cmd = base_cmd + ["--ligand_index", str(batch)]
        n_done = len(list(RESULTS_DIR.glob("*.pdbqt")))
        print(f"  Batch {j + 1}/{len(batches)} | results so far: {n_done}", flush=True)

        result = subprocess.run(
            cmd, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            text=True, timeout=7200,
        )

        if result.returncode == 139:
            print(f"  WARNING: Segfault on batch {j + 1} — skipping")
        elif result.returncode != 0:
            print(f"  WARNING: Batch {j + 1} exit code {result.returncode}")
            if result.stderr:
                print(f"    stderr: ...{result.stderr[-200:]}")

    elapsed = time.time() - t0
    n_results = len(list(RESULTS_DIR.glob("*.pdbqt")))
    print(f"  Docking complete: {n_results} results in {elapsed:.1f}s")

    # Cleanup batches
    shutil.rmtree(batch_dir)

    return elapsed


# ── Score transform ──────────────────────────────────────────────────────────

def apply_score_transform(scores):
    """
    Apply post-processing transform to scores.

    Transforms available:
      none   – raw negated Vina scores (higher = better)
      rank   – rank-based (ties get average rank)
      zscore – z-score normalization
      minmax – min-max scaling to [0, 1]
    """
    method = CONFIG["score_transform"]
    if method == "none" or not scores:
        return scores

    cids = sorted(scores.keys())
    vals = [scores[c] for c in cids]

    if method == "rank":
        import numpy as np
        order = np.argsort(vals)
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(1, len(vals) + 1, dtype=float)
        return {c: float(r) for c, r in zip(cids, ranks)}

    elif method == "zscore":
        z = scipy_zscore(vals)
        return {c: float(v) for c, v in zip(cids, z)}

    elif method == "minmax":
        lo, hi = min(vals), max(vals)
        rng = hi - lo if hi != lo else 1.0
        return {c: (v - lo) / rng for c, v in zip(cids, vals)}

    else:
        print(f"  WARNING: Unknown transform '{method}', using raw scores")
        return scores


# ── Main pipeline ────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  VS Autoresearch Experiment")
    print("=" * 55)
    print(f"  Library:        {CONFIG['library']}")
    print(f"  Receptor:       {CONFIG['receptor']}")
    print(f"  Box size:       {CONFIG['box_size']}A")
    print(f"  Exhaustiveness: {CONFIG['exhaustiveness']}")
    print(f"  Scoring:        {CONFIG['scoring']}")
    print(f"  Transform:      {CONFIG['score_transform']}")
    print()

    # Run docking (or reuse existing results)
    if CONFIG["reuse_results"]:
        n_results = len(list(RESULTS_DIR.glob("*.pdbqt")))
        print(f"  Reusing {n_results} existing results (skip docking)")
        elapsed = 0.0
    else:
        elapsed = run_docking()

    # Parse results
    print("\nParsing results...")
    scores = parse_unidock_results(RESULTS_DIR)
    print(f"  Parsed {len(scores)} compound scores")

    # Apply transform
    if CONFIG["score_transform"] != "none":
        print(f"\nApplying transform: {CONFIG['score_transform']}")
        scores = apply_score_transform(scores)

    # Evaluate
    print("\n--- Metrics ---")
    metrics = evaluate(scores)

    # Summary
    print(f"\ntime: {elapsed:.1f}s")

    return metrics


if __name__ == "__main__":
    main()
