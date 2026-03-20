#!/usr/bin/env python3
"""
CDK2 Autoresearch – Experiment file (agent-modified).

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
    # Library choice: "skill" (Meeko+PAINS-filtered) or "naive" (OpenBabel)
    "library": "naive",

    # Receptor choice: "skill" (Meeko mk_prepare_receptor) or "naive" (OpenBabel)
    "receptor": "skill",

    # Search box (angstroms) centered on CDK2 binding site
    "box_size": 25,

    # Sampling thoroughness (higher = more exhaustive, slower)
    "exhaustiveness": 8,

    # Number of binding modes to generate per ligand
    "num_modes": 10,

    # Energy range for keeping poses (kcal/mol above best)
    "energy_range": 3,

    # Scoring function: "vina" or "vinardo"
    "scoring": "vina",

    # GPU device index (use "0,1" for both GPUs)
    "gpu_device": "0,1",

    # Post-processing score transform: "none", "rank", "zscore", "minmax"
    "score_transform": "none",

    # Batch size for Uni-Dock (smaller = fewer ligands lost per segfault)
    "batch_size": 50,

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
    Supports dual-GPU via CUDA_VISIBLE_DEVICES.
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

    # Check if using multiple GPUs
    gpu_devices = CONFIG["gpu_device"].split(",")
    n_gpus = len(gpu_devices)

    if n_gpus > 1:
        # Split ligands across GPUs
        per_gpu = len(lines) // n_gpus
        gpu_line_groups = []
        for g in range(n_gpus):
            start = g * per_gpu
            end = len(lines) if g == n_gpus - 1 else (g + 1) * per_gpu
            gpu_line_groups.append((gpu_devices[g], lines[start:end]))
        print(f"  {n_ligands} ligands split across {n_gpus} GPUs")
        return run_docking_multi_gpu(gpu_line_groups, batch_size)
    else:
        return run_docking_single_gpu(lines, batch_size, gpu_devices[0])


def run_docking_single_gpu(lines, batch_size, gpu_device):
    """Run docking on a single GPU."""
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

    print(f"  {len(lines)} ligands in {len(batches)} batches of {batch_size} (GPU {gpu_device})")

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = gpu_device

    cx, cy, cz = BOX_CENTER
    sz = str(CONFIG["box_size"])

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

    shutil.rmtree(batch_dir)
    return elapsed


def run_docking_multi_gpu(gpu_line_groups, batch_size):
    """Run docking across multiple GPUs in parallel using subprocesses."""
    import multiprocessing

    cx, cy, cz = BOX_CENTER
    sz = str(CONFIG["box_size"])

    # Create per-GPU results dirs and batch files
    gpu_tasks = []
    for gpu_id, gpu_lines in gpu_line_groups:
        gpu_batch_dir = CACHE_DIR / f"batches_gpu{gpu_id}"
        if gpu_batch_dir.exists():
            shutil.rmtree(gpu_batch_dir)
        gpu_batch_dir.mkdir()

        batches = []
        for i in range(0, len(gpu_lines), batch_size):
            bp = gpu_batch_dir / f"batch_{i:05d}.txt"
            bp.write_text("\n".join(gpu_lines[i:i + batch_size]) + "\n")
            batches.append(bp)

        print(f"  GPU {gpu_id}: {len(gpu_lines)} ligands in {len(batches)} batches")
        gpu_tasks.append((gpu_id, batches, gpu_batch_dir))

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
    if CONFIG["scoring"] != "vina":
        base_cmd.extend(["--scoring", CONFIG["scoring"]])

    def run_gpu(gpu_id, batches):
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = gpu_id
        for j, batch in enumerate(batches):
            cmd = base_cmd + ["--ligand_index", str(batch)]
            result = subprocess.run(
                cmd, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                text=True, timeout=7200,
            )
            if result.returncode == 139:
                print(f"  GPU {gpu_id} batch {j+1}/{len(batches)}: segfault — skipping")
            elif result.returncode != 0:
                print(f"  GPU {gpu_id} batch {j+1}/{len(batches)}: exit {result.returncode}")

    t0 = time.time()

    # Launch GPU workers in parallel
    processes = []
    for gpu_id, batches, _ in gpu_tasks:
        p = multiprocessing.Process(target=run_gpu, args=(gpu_id, batches))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    elapsed = time.time() - t0
    n_results = len(list(RESULTS_DIR.glob("*.pdbqt")))
    print(f"  Docking complete: {n_results} results in {elapsed:.1f}s (dual-GPU)")

    # Cleanup
    for _, _, gpu_batch_dir in gpu_tasks:
        shutil.rmtree(gpu_batch_dir, ignore_errors=True)

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
    print("  CDK2 Autoresearch Experiment")
    print("=" * 55)
    print(f"  Library:        {CONFIG['library']}")
    print(f"  Receptor:       {CONFIG['receptor']}")
    print(f"  Box size:       {CONFIG['box_size']}A")
    print(f"  Exhaustiveness: {CONFIG['exhaustiveness']}")
    print(f"  Scoring:        {CONFIG['scoring']}")
    print(f"  Transform:      {CONFIG['score_transform']}")
    print(f"  GPU:            {CONFIG['gpu_device']}")
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
